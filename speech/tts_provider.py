"""Abstract base class for TTS providers."""

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

from .audio_manager import AudioManager


class TTSProviderAbstract(ABC):
    """Abstract base class for all TTS providers."""

    def __init__(self, config: dict | None = None):
        """Initialize the TTS provider with audio management."""
        self.audio_manager = AudioManager()
        self.logger = logging.getLogger(__name__)
        self._voice_cache: dict[str, list[dict[str, Any]]] = {}
        self._on_start: Callable | None = None
        self._on_stop: Callable | None = None
        self._on_complete: Callable | None = None
        self._was_stopped = False

        # Setup caching
        self.config = config or {}
        self._cache_enabled = self.config.get("General", {}).get("cache_enabled", True)
        self._cache_dir = Path(self.config.get("General", {}).get("cache_dir", "temp"))
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._audio_cache_dir = self._cache_dir / "audio"
        self._audio_cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, text: str, voice_id: str) -> str:
        """Generate cache key for audio data."""
        # Create a unique key based on text and voice
        key_data = f"{text}:{voice_id}".encode()
        return hashlib.md5(key_data).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path for cached audio file."""
        return self._audio_cache_dir / f"{cache_key}.wav"

    def _get_metadata_path(self, cache_key: str) -> Path:
        """Get path for cached metadata file."""
        return self._audio_cache_dir / f"{cache_key}.json"

    def _cache_audio_data(
        self, cache_key: str, audio_data: bytes, metadata: dict
    ) -> None:
        """Cache audio data and metadata."""
        if not self._cache_enabled:
            return

        try:
            # Save audio data
            audio_path = self._get_cache_path(cache_key)
            with open(audio_path, "wb") as f:
                f.write(audio_data)

            # Save metadata
            meta_path = self._get_metadata_path(cache_key)
            with open(meta_path, "w") as f:
                json.dump(metadata, f)

            self.logger.debug(f"Cached audio data for key: {cache_key}")
        except Exception as e:
            self.logger.error(f"Error caching audio data: {e}")

    def _get_cached_audio(self, cache_key: str) -> bytes | None:
        """Get cached audio data if available."""
        if not self._cache_enabled:
            return None

        try:
            audio_path = self._get_cache_path(cache_key)
            meta_path = self._get_metadata_path(cache_key)

            if audio_path.exists() and meta_path.exists():
                # Load metadata to verify cache validity
                with open(meta_path) as f:
                    json.load(f)

                # TODO: Add cache validation based on metadata
                # For now, just return the cached audio
                with open(audio_path, "rb") as f:
                    audio_data = f.read()
                self.logger.debug(f"Using cached audio data for key: {cache_key}")
                return audio_data
        except Exception as e:
            self.logger.error(f"Error reading cached audio: {e}")
        return None

    def get_speak_data(self, text: str, voice_id: str) -> bytes | None:
        """Get audio data for text, using cache if available."""
        # If caching is disabled, just generate new audio
        if not self._cache_enabled:
            return self._generate_speak_data(text, voice_id)

        # Try to get from cache first
        cache_key = self._get_cache_key(text, voice_id)
        cached_data = self._get_cached_audio(cache_key)
        if cached_data:
            return cached_data

        # If not in cache, generate new audio data
        audio_data = self._generate_speak_data(text, voice_id)
        if audio_data:
            # Cache the new audio data
            metadata = {"text": text, "voice_id": voice_id, "timestamp": time.time()}
            self._cache_audio_data(cache_key, audio_data, metadata)
        return audio_data

    @abstractmethod
    def _generate_speak_data(self, text: str, voice_id: str) -> bytes | None:
        """Generate audio data for text. Must be implemented by concrete providers.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use

        Returns:
            Audio data as bytes, or None if synthesis failed
        """
        pass

    def speak(
        self, text: str, voice_id: str, on_complete: Callable | None = None
    ) -> bool:
        """Speak text using specified voice.

        Args:
            text: Text to speak
            voice_id: Voice ID to use
            on_complete: Optional callback when playback completes

        Returns:
            True if audio started playing, False if error occurred
        """
        try:
            # Get audio data from concrete implementation
            audio_data = self.get_speak_data(text, voice_id)
            if not audio_data:
                raise RuntimeError("Failed to generate audio data")

            # Set up completion callback that handles both natural completion and stops
            def on_audio_complete():
                if self._on_stop:
                    self._on_stop()
                if not self._was_stopped and self._on_complete:
                    self._on_complete()
                if not self._was_stopped and on_complete:
                    on_complete()
                self._was_stopped = False

            # Set up start callback
            def on_audio_start():
                if self._on_start:
                    self._on_start()

            # Reset stop flag
            self._was_stopped = False

            # Start playback with callbacks
            success = self.audio_manager.play_audio(
                audio_data, on_complete=on_audio_complete, on_start=on_audio_start
            )

            return success

        except Exception as e:
            self.logger.error(f"Error in speak: {e}")
            if on_complete:
                on_complete()
            return False

    @abstractmethod
    def get_voices(self, langcodes: str = "bcp47") -> list[dict[str, Any]]:
        """Get available voices with specified language code format.

        Args:
            langcodes: Language code format to return. Options are:
                - "bcp47": BCP-47 format (default)
                - "iso639_3": ISO 639-3 format
                - "display": Human-readable display names
                - "all": All formats in a dictionary

        Returns:
            List of voice dictionaries with standardized format.

            For bcp47, iso639_3, and display formats:
            {
                "id": str,
                "name": str,
                "language_codes": list[str],  # Format depends on langcodes parameter
                "gender": str
            }

            For "all" format:
            {
                "id": str,
                "name": str,
                "language_codes": {  # Dictionary of language codes
                    "<lang_code>": {
                        "bcp47": str,
                        "iso639_3": str,
                        "display": str
                    }
                },
                "gender": str
            }
        """
        pass

    @lru_cache(maxsize=100)
    def _get_cached_voices(self, langcodes: str = "bcp47") -> list[dict[str, Any]]:
        """Get cached list of voices, fetching from provider if not cached.

        Args:
            langcodes: Language code format to return

        Returns:
            List of voice dictionaries
        """
        return self.get_voices(langcodes=langcodes)

    def get_cached_voices(
        self, force_refresh: bool = False, langcodes: str = "bcp47"
    ) -> list[dict[str, Any]]:
        """Get list of available voices, using cache if available.

        Args:
            force_refresh: If True, ignore cache and fetch fresh data
            langcodes: Language code format to return

        Returns:
            List of voice dictionaries
        """
        if force_refresh:
            # Clear the cache and fetch fresh data
            self._get_cached_voices.cache_clear()

        return self._get_cached_voices(langcodes=langcodes)

    def stop_speaking(self) -> None:
        """Stop current speech playback."""
        if self.is_speaking:
            self._was_stopped = True
            self.audio_manager.stop()
            if self._on_stop:
                self._on_stop()

    @property
    def is_speaking(self) -> bool:
        """Check if audio is currently playing.

        Returns:
            True if audio is playing, False otherwise
        """
        return self.audio_manager.is_playing

    def set_speech_handlers(
        self,
        on_start: Callable | None = None,
        on_stop: Callable | None = None,
        on_complete: Callable | None = None,
    ) -> None:
        """Set handlers for speech events.

        Args:
            on_start: Called when speech starts
            on_stop: Called when speech is stopped (manually or naturally)
            on_complete: Called only when speech completes naturally
        """
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_complete = on_complete
