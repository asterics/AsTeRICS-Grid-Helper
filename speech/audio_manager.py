"""Audio playback manager for TTS providers."""

import logging
from pathlib import Path
from typing import Optional, Callable, Any
import hashlib
import tempfile
import threading
import time
import queue
import weakref
import subprocess
import os
import sys

import numpy as np
import sounddevice as sd
import soundfile as sf

logger = logging.getLogger(__name__)


class AudioManager:
    """Manages audio playback and caching."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize audio manager.

        Args:
            cache_dir: Optional directory for caching audio files. If None,
                      uses system temp directory.
        """
        self._stream: Optional[sd.OutputStream] = None
        self._is_playing = False
        self._on_complete: Optional[Callable] = None
        self._on_start: Optional[Callable] = None
        self._stream_lock = threading.RLock()
        self._callback_error = None
        self._last_callback_time = 0
        self._cleanup_event = threading.Event()
        self._stream_queue = queue.Queue()
        self.logger = logging.getLogger(__name__)

        # Setup cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._stream_cleanup_worker, daemon=True
        )
        self._cleanup_thread.start()

        # Setup caching
        if cache_dir:
            self._cache_dir = Path(cache_dir)
        else:
            self._cache_dir = Path(tempfile.gettempdir()) / "tts_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache size limit (100MB)
        self._cache_size_limit = 100 * 1024 * 1024

    def _stream_cleanup_worker(self):
        """Worker thread for safe stream cleanup."""
        while True:
            try:
                stream = self._stream_queue.get(timeout=0.5)
                if stream is None:  # Shutdown signal
                    break
                try:
                    stream.stop()
                except:
                    pass
                time.sleep(0.05)  # Short delay
                try:
                    stream.close()
                except:
                    pass
            except queue.Empty:
                if self._cleanup_event.is_set():
                    break
                continue
            except Exception as e:
                self.logger.debug(f"Cleanup worker error: {str(e)}")

    def _get_cache_key(self, audio_data: bytes) -> str:
        """Generate cache key from audio data."""
        return hashlib.md5(audio_data).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path for cached audio file."""
        return self._cache_dir / f"{cache_key}.wav"

    def _cache_audio(self, audio_data: bytes) -> Optional[Path]:
        """Cache audio data to file."""
        try:
            # Check cache size and clean if needed
            self._clean_cache_if_needed()

            # Generate cache key and path
            cache_key = self._get_cache_key(audio_data)
            cache_path = self._get_cache_path(cache_key)

            # Skip if already cached
            if cache_path.exists():
                return cache_path

            # Write to cache
            with open(cache_path, "wb") as f:
                f.write(audio_data)

            return cache_path

        except Exception as e:
            self.logger.error(f"Error caching audio: {e}")
            return None

    def _clean_cache_if_needed(self) -> None:
        """Clean oldest cache files if total size exceeds limit."""
        try:
            # Get cache files sorted by modification time
            cache_files = sorted(
                self._cache_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime
            )

            # Calculate total size
            total_size = sum(p.stat().st_size for p in cache_files)

            # Remove oldest files until under limit
            while total_size > self._cache_size_limit and cache_files:
                file_to_remove = cache_files.pop(0)
                total_size -= file_to_remove.stat().st_size
                file_to_remove.unlink()

        except Exception as e:
            self.logger.error(f"Error cleaning cache: {e}")

    def _load_audio_data(self, audio_data: bytes) -> tuple[np.ndarray, int]:
        """Load and normalize audio data.

        Args:
            audio_data: WAV format audio data

        Returns:
            Tuple of (normalized audio array, sample rate)
        """
        # Try to get cached file
        cache_path = self._cache_audio(audio_data)
        if cache_path and cache_path.exists():
            # Load from cache
            data, samplerate = sf.read(str(cache_path))
        else:
            # Load directly from bytes
            with tempfile.NamedTemporaryFile(suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                data, samplerate = sf.read(temp_file.name)

        # Ensure data is float32
        if data.dtype != np.float32:
            data = data.astype(np.float32)

        # Ensure 2D array for both mono and stereo
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)

        return data, samplerate

    def _safe_stream_operation(self, operation: Callable) -> bool:
        """Safely perform a stream operation with proper locking and error handling.

        Args:
            operation: Function that performs the stream operation

        Returns:
            bool: True if operation succeeded
        """
        if not self._stream_lock.acquire(
            timeout=0.5
        ):  # Add timeout to prevent deadlock
            self.logger.warning("Could not acquire stream lock - timeout")
            return False

        try:
            if self._stream is not None:
                try:
                    operation()
                    return True
                except Exception as e:
                    self.logger.debug(f"Stream operation failed: {str(e)}")
            return False
        finally:
            try:
                self._stream_lock.release()
            except:
                pass

    def _create_stream(
        self,
        samplerate: int,
        channels: int,
        callback: Callable,
        finished_callback: Callable,
    ) -> bool:
        """Create audio output stream with error handling.

        Returns:
            bool: True if stream was created successfully
        """
        if not self._stream_lock.acquire(timeout=0.5):
            self.logger.warning("Could not acquire stream lock for creation - timeout")
            return False

        try:
            # Ensure old stream is cleaned up
            if self._stream is not None:
                self._stream_queue.put(self._stream)
                self._stream = None

            try:
                self._stream = sd.OutputStream(
                    samplerate=samplerate,
                    channels=channels,
                    callback=callback,
                    finished_callback=finished_callback,
                )
                return True
            except Exception as e:
                self.logger.error(f"Error creating audio stream: {str(e)}")
                self._stream = None
                return False
        finally:
            try:
                self._stream_lock.release()
            except:
                pass

    def _check_stream_timeout(self) -> None:
        """Check if stream has timed out and clean up if needed."""
        if (
            self._is_playing and time.time() - self._last_callback_time > 2.0
        ):  # 2 second timeout
            self.logger.warning("Audio stream timeout detected - forcing cleanup")
            self.stop()

    def play_audio(
        self,
        audio_data: bytes,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> bool:
        """Play audio data through system speakers.

        Args:
            audio_data: Audio data as bytes
            on_complete: Optional callback when playback completes
            on_error: Optional callback when an error occurs

        Returns:
            True if audio started playing, False if error occurred
        """
        try:
            logger.debug("Starting audio playback in AudioManager")
            logger.debug(f"Audio data size: {len(audio_data)} bytes")
            logger.debug(f"on_complete callback: {on_complete}")
            logger.debug(f"on_error callback: {on_error}")

            # Create a temporary file for the audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            logger.debug(f"Created temporary audio file: {temp_path}")

            # Use platform-specific audio playback command
            if sys.platform == "darwin":  # macOS
                cmd = ["afplay", temp_path]
            elif sys.platform == "linux":
                cmd = ["aplay", temp_path]
            elif sys.platform == "win32":  # Windows
                # Use PowerShell to play audio
                cmd = [
                    "powershell",
                    "-c",
                    f"Add-Type -AssemblyName Media.SoundPlayer; (New-Object Media.SoundPlayer '{temp_path}').PlaySync()",
                ]
            else:
                raise RuntimeError(f"Unsupported platform: {sys.platform}")

            logger.debug(f"Using audio command: {' '.join(cmd)}")

            # Set up the audio process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Start monitoring thread
            self._monitor_thread = threading.Thread(
                target=self._monitor_playback,
                args=(temp_path, on_complete, on_error),
            )
            self._monitor_thread.daemon = True
            self._monitor_thread.start()

            logger.debug("Started audio playback monitoring thread")
            return True

        except Exception as e:
            logger.error(f"Error starting audio playback: {e}", exc_info=True)
            if on_error:
                try:
                    logger.debug("Calling error callback")
                    on_error(e)
                except Exception as callback_error:
                    logger.error(
                        f"Error in error callback: {callback_error}", exc_info=True
                    )
            return False

    def _monitor_playback(
        self,
        temp_path: str,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> None:
        """Monitor audio playback process.

        Args:
            temp_path: Path to temporary audio file
            on_complete: Optional callback when playback completes
            on_error: Optional callback when an error occurs
        """
        try:
            logger.debug("Starting playback monitoring")
            stdout, stderr = self.process.communicate()

            # Clean up temporary file
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {e}")

            if self.process.returncode == 0:
                logger.debug("Audio playback completed normally")
                if on_complete:
                    try:
                        logger.debug("Calling completion callback")
                        on_complete()
                    except Exception as e:
                        logger.error(
                            f"Error in completion callback: {e}", exc_info=True
                        )
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Audio playback failed: {error_msg}")
                if on_error:
                    try:
                        logger.debug("Calling error callback")
                        on_error(error_msg)
                    except Exception as e:
                        logger.error(f"Error in error callback: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in playback monitoring: {e}", exc_info=True)
            if on_error:
                try:
                    logger.debug("Calling error callback")
                    on_error(e)
                except Exception as callback_error:
                    logger.error(
                        f"Error in error callback: {callback_error}", exc_info=True
                    )

    def stop(self) -> None:
        """Stop current audio playback."""
        if not self._stream_lock.acquire(timeout=0.5):
            self.logger.warning("Could not acquire stream lock for stop - timeout")
            return

        try:
            if self._stream is not None:
                # Queue the stream for cleanup rather than handling it directly
                self._stream_queue.put(self._stream)
                self._stream = None

            # Reset state
            self._is_playing = False
            self._callback_error = None

        finally:
            try:
                self._stream_lock.release()
            except:
                pass

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        with self._stream_lock:
            # Check for timeout
            self._check_stream_timeout()
            # Ensure state consistency
            if self._stream is None and self._is_playing:
                self._is_playing = False
            return self._is_playing

    def __del__(self):
        """Cleanup on deletion."""
        self._cleanup_event.set()
        if self._stream is not None:
            try:
                self._stream_queue.put(None)  # Signal cleanup thread to stop
                self._cleanup_thread.join(timeout=1.0)  # Wait for cleanup with timeout
            except:
                pass
