#!/usr/bin/env python

import logging

from speech.provider_factory import TTSProviderFactory

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Test the TTS provider factory."""
    # Create provider factory
    provider_factory = TTSProviderFactory()

    # Create a simple config with just espeak
    config = {
        "engines": ["espeak"],
        "cache_enabled": True,
        "cache_dir": "temp",
        "engine_configs": {
            "espeak": {}
        }
    }

    # Create provider
    provider = provider_factory.create_provider("espeak", config)
    if provider:
        logger.info("Successfully created espeak provider")

        # Test getting voices
        voices = provider.get_voices()
        logger.info(f"Got {len(voices)} voices")

        # Test speaking
        text = "Hello, world!"
        voice_id = voices[0]["id"] if voices else None
        logger.info(f"Speaking with voice: {voice_id}")

        # Test get_speak_data
        audio_data = provider.get_speak_data(text, voice_id)
        if audio_data:
            logger.info(f"Got audio data: {len(audio_data)} bytes")
        else:
            logger.error("Failed to get audio data")
    else:
        logger.error("Failed to create espeak provider")

if __name__ == "__main__":
    main()
