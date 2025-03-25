"""Test audio playback and event handling with sherpaonnx."""

import asyncio
import logging
from pathlib import Path
from speech.provider_factory import TTSProviderFactory
from speech.audio_manager import AudioManager

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test configuration matching settings.ini structure
config = {
    "General": {
        "engines": ["sherpaonnx"],  # Only test sherpaonnx
        "cache_enabled": True,
        "cache_dir": "temp",
    }
}


async def test_audio_playback():
    """Test audio playback with sherpaonnx."""
    # Create provider and audio manager
    factory = TTSProviderFactory()
    provider = factory.create_provider("sherpaonnx", config)
    audio_manager = AudioManager()

    # Test text
    long_text = (
        "This is a long test sentence that should take several seconds to "
        "speak. We want to make sure we can stop it in the middle."
    )
    short_text = "Short test."

    # Event flags
    long_text_started = asyncio.Event()
    long_text_stopped = asyncio.Event()
    short_text_started = asyncio.Event()
    short_text_completed = asyncio.Event()
    cached_text_started = asyncio.Event()
    cached_text_completed = asyncio.Event()

    def on_long_start():
        logger.info("Long text started playing")
        long_text_started.set()

    def on_long_stop():
        logger.info("Long text stopped")
        long_text_stopped.set()

    def on_short_start():
        logger.info("Short text started playing")
        short_text_started.set()

    def on_short_complete():
        logger.info("Short text completed")
        short_text_completed.set()

    def on_cached_start():
        logger.info("Cached text started playing")
        cached_text_started.set()

    def on_cached_complete():
        logger.info("Cached text completed")
        cached_text_completed.set()

    try:
        # First test: Long text with stop
        logger.info("=== Starting first test: Long text with stop ===")
        # Get audio data for long text
        logger.info("Getting audio data for long text...")
        audio_data = provider.get_speak_data(long_text, "mms_eng")

        # Start playing long text
        logger.info("Starting long text playback...")
        provider.set_speech_handlers(on_start=on_long_start, on_stop=on_long_stop)
        success = audio_manager.play_audio(
            audio_data,
            on_start=on_long_start,
            on_complete=on_long_stop,
        )

        if not success:
            logger.error("Failed to start long text playback")
            return

        # Wait for playback to start with timeout
        try:
            await asyncio.wait_for(long_text_started.wait(), timeout=2.0)
            logger.info("Long text playback started")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for playback to start")
            audio_manager.stop()
            return

        # Wait a bit then stop
        await asyncio.sleep(2.0)
        logger.info("Stopping long text playback...")
        audio_manager.stop()
        long_text_stopped.set()

        # Wait for stop event with timeout
        try:
            await asyncio.wait_for(long_text_stopped.wait(), timeout=2.0)
            logger.info("Long text playback stopped")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for playback to stop")
            return

        # Short delay to ensure cleanup
        await asyncio.sleep(0.5)

        # Second test: Short text with completion
        logger.info("=== Starting second test: Short text with completion ===")
        # Get audio data for short text
        logger.info("Getting audio data for short text...")
        audio_data = provider.get_speak_data(short_text, "mms_eng")

        # Start playing short text
        logger.info("Starting short text playback...")
        provider.set_speech_handlers(
            on_start=on_short_start, on_complete=on_short_complete
        )
        success = audio_manager.play_audio(
            audio_data, on_start=on_short_start, on_complete=on_short_complete
        )

        if not success:
            logger.error("Failed to start short text playback")
            return

        # Wait for short text to start with timeout
        try:
            await asyncio.wait_for(short_text_started.wait(), timeout=2.0)
            logger.info("Short text playback started")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for short text to start")
            audio_manager.stop()
            return

        # Wait for completion with timeout
        try:
            await asyncio.wait_for(short_text_completed.wait(), timeout=5.0)
            logger.info("Short text playback completed")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for short text to complete")
            audio_manager.stop()
            return

        # Third test: Cached audio playback
        logger.info("=== Starting third test: Cached audio playback ===")
        # Get the same audio data again - should use cache
        logger.info("Getting cached audio data for short text...")
        cached_audio_data = provider.get_speak_data(short_text, "mms_eng")

        # Start playing cached audio
        logger.info("Starting cached audio playback...")
        provider.set_speech_handlers(
            on_start=on_cached_start, on_complete=on_cached_complete
        )
        success = audio_manager.play_audio(
            cached_audio_data, on_start=on_cached_start, on_complete=on_cached_complete
        )

        if not success:
            logger.error("Failed to start cached audio playback")
            return

        # Wait for cached audio to start with timeout
        try:
            await asyncio.wait_for(cached_text_started.wait(), timeout=2.0)
            logger.info("Cached audio playback started")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for cached audio to start")
            audio_manager.stop()
            return

        # Wait for completion with timeout
        try:
            await asyncio.wait_for(cached_text_completed.wait(), timeout=5.0)
            logger.info("Cached audio playback completed")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for cached audio to complete")
            audio_manager.stop()
            return

        logger.info("All tests completed successfully")

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        audio_manager.stop()
    finally:
        # Ensure cleanup
        audio_manager.stop()


if __name__ == "__main__":
    try:
        asyncio.run(test_audio_playback())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
