#!/usr/bin/env python

"""Test audio playback and event handling with sherpaonnx."""

import asyncio
import logging

from speech.provider_factory import TTSProviderFactory

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test texts
LONG_TEXT = (
    "This is a long test sentence that should take several seconds to "
    "speak. We want to make sure we can stop it in the middle."
)
SHORT_TEXT = "Short test."
MULTIPLE_TEXTS = [
    "First test sentence.",
    "Second test sentence.",
    "Third test sentence.",
]


async def test_audio_playback():
    """Test audio playback and event handling with TTS provider."""
    provider = None
    try:
        # Create config with only sherpaonnx
        config = {
            "General": {
                "engines": ["sherpaonnx"],  # Only test sherpaonnx
                "cache_enabled": True,
                "cache_dir": "temp",
            },
            "engine_configs": {
                "sherpaonnx": {
                    "voice": "mms_eng",  # Default English voice
                    "lang": "en",  # English language
                }
            },
        }
        logger.debug(f"Using config: {config}")

        # Initialize provider with sherpaonnx
        provider = TTSProviderFactory.create_provider("sherpaonnx", config)
        if not provider:
            logger.error("Failed to create provider")
            return

        # Get available voices
        voices = provider.get_voices()
        if not voices:
            logger.error("No voices available")
            return

        # Use first available voice
        voice_id = voices[0]["id"]
        logger.info(f"Using voice: {voice_id}")

        # Event flags for state tracking
        long_text_started = asyncio.Event()
        long_text_stopped = asyncio.Event()
        short_text_started = asyncio.Event()
        short_text_completed = asyncio.Event()

        # Test 1: Long text with stop
        logger.info("=== Starting first test: Long text with stop ===")
        long_text = "This is a long text that will be played and then stopped."

        def on_start():
            logger.info("Long text started playing")
            long_text_started.set()

        def on_stop():
            logger.info("Long text stopped")
            long_text_stopped.set()

        def on_complete():
            logger.info("Long text playback completed")

        def on_error(error):
            logger.error(f"Long text playback error: {error}")

        success = provider.speak(
            long_text,
            voice_id,
            on_start=on_start,
            on_stop=on_stop,
            on_complete=on_complete,
            on_error=on_error,
        )
        if not success:
            logger.error("Failed to start long text playback")
            return

        # Wait for start with timeout
        try:
            await asyncio.wait_for(long_text_started.wait(), timeout=10.0)
        except TimeoutError:
            logger.error("Timeout waiting for long text to start")
            return

        # Wait a bit then stop
        await asyncio.sleep(2)
        logger.info("Stopping playback...")
        provider.stop_speaking()

        # Wait for stop with timeout
        try:
            await asyncio.wait_for(long_text_stopped.wait(), timeout=10.0)
        except TimeoutError:
            logger.error("Timeout waiting for long text to stop")
            return

        # Test 2: Short text
        logger.info("\n=== Starting second test: Short text ===")
        short_text = "This is a short test."

        def on_start():
            logger.info("Short text started playing")
            short_text_started.set()

        def on_complete():
            logger.info("Short text completed")
            short_text_completed.set()

        def on_error(error):
            logger.error(f"Short text playback error: {error}")

        success = provider.speak(
            short_text,
            voice_id,
            on_start=on_start,
            on_complete=on_complete,
            on_error=on_error,
        )
        if not success:
            logger.error("Failed to start short text playback")
            return

        # Wait for completion with timeout
        try:
            await asyncio.wait_for(short_text_completed.wait(), timeout=10.0)
        except TimeoutError:
            logger.error("Timeout waiting for short text to complete")
            return

        # Test 3: Multiple short texts
        logger.info("\n=== Starting third test: Multiple short texts ===")
        texts = ["First text.", "Second text.", "Third text."]

        for i, text in enumerate(texts, 1):
            logger.info(f"Getting audio data for text {i}...")

            text_started = asyncio.Event()
            text_completed = asyncio.Event()

            def on_start():
                logger.info(f"Text {i} started playing")
                text_started.set()

            def on_complete():
                logger.info(f"Text {i} completed")
                text_completed.set()

            def on_error(error):
                logger.error(f"Text {i} playback error: {error}")

            logger.info(f"Starting Text {i} playback...")
            success = provider.speak(
                text,
                voice_id,
                on_start=on_start,
                on_complete=on_complete,
                on_error=on_error,
            )
            if not success:
                logger.error(f"Failed to start text {i} playback")
                continue

            # Wait for completion with timeout
            try:
                await asyncio.wait_for(text_completed.wait(), timeout=10.0)
            except TimeoutError:
                logger.error(f"Timeout waiting for text {i} to complete")
                provider.stop_speaking()
                break

        logger.info("\nAll tests completed successfully!")

    except Exception as e:
        logger.error(f"Test error: {e}", exc_info=True)
    finally:
        # Cleanup
        if provider and provider.is_speaking:
            provider.stop_speaking()


if __name__ == "__main__":
    asyncio.run(test_audio_playback())
