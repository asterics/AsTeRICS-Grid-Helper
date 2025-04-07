#!/usr/bin/env python

"""Test harness for TTS providers."""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any

from speech.audio_manager import AudioManager
from speech.config_manager import ConfigManager
from speech.provider_factory import TTSProviderFactory
from speech.tts_provider import TTSProviderAbstract

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("testengines.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Set up summary logging
summary_logger = logging.getLogger("summary")
summary_handler = logging.FileHandler("test_summary.log")
summary_handler.setFormatter(logging.Formatter("%(message)s"))
summary_logger.addHandler(summary_handler)
summary_logger.setLevel(logging.INFO)

# Test text
TEST_TEXT = "This is a test sentence for the TTS engine."

# Create audio manager instance
audio_manager = AudioManager()


def log_summary(message: str) -> None:
    """Log a message to both the summary file and console."""
    print(message)
    summary_logger.info(message)


class EngineTester:
    """Test harness for TTS providers."""

    def __init__(self) -> None:
        """Initialize the engine tester."""
        self.config_manager = ConfigManager()
        self.providers: dict[str, TTSProviderAbstract] = {}
        self.test_text = "Hello! This is a test of the text-to-speech system."
        self.summary_data: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "providers": {},
        }

        # Initialize providers using factory
        self._init_providers()

    def _init_providers(self) -> None:
        """Initialize all configured providers using the factory."""
        config = self.config_manager.get_tts_config()
        for engine_type in config.get("engines", []):
            provider = TTSProviderFactory.create_provider(engine_type, config)
            if provider:
                self.providers[engine_type] = provider
                logger.info(f"Successfully initialized {engine_type} provider")
            else:
                logger.error(f"Failed to initialize {engine_type} provider")

    def check_credentials(self, provider_id: str) -> bool:
        """Check if credentials are valid for a provider.

        Args:
            provider_id: The ID of the provider to check.

        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        try:
            if provider_id not in self.providers:
                logger.warning(f"Provider {provider_id} not found")
                return False

            provider = self.providers[provider_id]
            # Try to get voices as a credential check
            voices = provider.get_voices()
            return bool(voices)
        except Exception as e:
            logger.error(f"Error checking credentials for {provider_id}: {e}")
            return False

    def print_voice_info(self, voice: dict[str, Any], provider_id: str) -> None:
        """Print detailed information about a voice.

        Args:
            voice: The voice information dictionary.
            provider_id: The ID of the provider.
        """
        logger.info(f"\nVoice from {provider_id}:")
        logger.info(f"  ID: {voice.get('id', 'N/A')}")
        logger.info(f"  Name: {voice.get('name', 'N/A')}")
        logger.info(f"  Language: {voice.get('language', 'N/A')}")
        logger.info(f"  Language Codes: {voice.get('language_codes', [])}")
        logger.info(f"  Gender: {voice.get('gender', 'N/A')}")

        # Check for potential issues
        issues = self._check_voice_issues(voice)
        if issues:
            logger.warning("  ⚠️ Issues found:")
            for issue in issues:
                logger.warning(f"    - {issue}")

    def _check_voice_issues(self, voice: dict[str, Any]) -> list[str]:
        """Check for potential issues in voice data.

        Args:
            voice: The voice information dictionary.

        Returns:
            List[str]: List of issues found.
        """
        issues = []
        if not voice.get("language"):
            issues.append("Missing language field")
        if not voice.get("language_codes"):
            issues.append("Missing language_codes")
        if any("\x02" in code for code in voice.get("language_codes", [])):
            issues.append("Contains \\x02 in language codes")
        if "\x02" in voice.get("language", ""):
            issues.append("Contains \\x02 in language field")
        return issues

    def _sanitize_voice_data(self, voice: dict) -> dict:
        """Sanitize voice data for JSON serialization.

        Args:
            voice: Voice data dictionary

        Returns:
            Sanitized voice data dictionary
        """
        # Create a new dict with only JSON-serializable values
        sanitized: dict[str, Any] = {}
        for key, value in voice.items():
            # Handle common types
            if isinstance(value, str | int | float | bool | type(None)):
                sanitized[key] = value
            # Handle lists/tuples
            elif isinstance(value, list | tuple):
                sanitized[key] = [
                    (
                        self._sanitize_voice_data(item)
                        if isinstance(item, dict)
                        else (
                            str(item)
                            if not isinstance(item, str | int | float | bool | type(None))
                            else item
                        )
                    )
                    for item in value
                ]
            # Handle dicts
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_voice_data(value)
            # Convert other types to strings
            else:
                sanitized[key] = str(value)
        return sanitized

    async def test_voice_reporting(self) -> None:
        """Test voice reporting from all providers."""
        logger.info("\n=== Testing Voice Reporting ===")

        for provider_id, provider in self.providers.items():
            logger.info(f"\nTesting provider: {provider_id}")

            # Check credentials first
            if not self.check_credentials(provider_id):
                logger.warning(f"  ⚠️ Invalid or missing credentials for {provider_id}")
                self.summary_data["providers"][provider_id] = {
                    "status": "error",
                    "error": "Invalid or missing credentials",
                }
                continue

            try:
                voices = provider.get_voices()
                logger.info(f"Found {len(voices)} voices")

                # Add to summary data with sanitized voice data
                self.summary_data["providers"][provider_id] = {
                    "status": "success",
                    "voice_count": len(voices),
                    "voices": [self._sanitize_voice_data(voice) for voice in voices],
                }

                for voice in voices:
                    self.print_voice_info(voice, provider_id)

            except Exception as e:
                logger.error(f"Error getting voices from {provider_id}: {e}")
                self.summary_data["providers"][provider_id] = {
                    "status": "error",
                    "error": str(e),
                }

    async def test_speech_functionality(self, provider_id: str, voice_id: str) -> None:
        """Test speech functionality for a specific provider and voice.

        Args:
            provider_id: The ID of the provider to test.
            voice_id: The ID of the voice to use.
        """
        logger.info(f"\n=== Testing Speech Functionality for {provider_id} ===")
        logger.info(f"Using voice: {voice_id}")

        try:
            provider = self.providers[provider_id]

            # Test getting speech data
            logger.info("Testing get_speak_data...")
            try:
                audio_data = provider.get_speak_data(self.test_text, voice_id)
                if not audio_data:
                    logger.error("Failed to get speech data - no data returned")
                    self.summary_data["providers"][provider_id][
                        "speech_test"
                    ] = "failed"
                    self.summary_data["providers"][provider_id][
                        "speech_error"
                    ] = "No audio data returned"
                    return
                logger.info(f"✓ Successfully got speech data ({len(audio_data)} bytes)")
            except Exception as e:
                logger.error(f"Failed to get speech data: {e!s}")
                self.summary_data["providers"][provider_id]["speech_test"] = "failed"
                self.summary_data["providers"][provider_id][
                    "speech_error"
                ] = f"Speech data error: {e!s}"
                return

            # Test 1: Basic speech with events
            logger.info("Testing speech events...")
            start_event = asyncio.Event()
            stop_event = asyncio.Event()
            complete_event = asyncio.Event()

            def on_start():
                logger.debug("Speech started callback triggered")
                start_event.set()

            def on_stop():
                logger.debug("Speech stopped callback triggered")
                stop_event.set()

            def on_complete():
                logger.debug("Speech completed callback triggered")
                complete_event.set()

            # Set up event handlers
            provider.set_speech_handlers(
                on_start=on_start,
                on_stop=on_stop,
                on_complete=on_complete,
            )

            # Start speaking
            logger.info("Starting speech test...")
            success = provider.speak(self.test_text, voice_id)
            if not success:
                logger.error("Failed to start speech")
                self.summary_data["providers"][provider_id]["speech_test"] = "failed"
                self.summary_data["providers"][provider_id][
                    "speech_error"
                ] = "Failed to start speech"
                return

            # Wait for speech to start
            try:
                await asyncio.wait_for(start_event.wait(), timeout=2)
                logger.info("✓ Speech started")
            except TimeoutError:
                logger.error("Speech did not start within timeout")
                provider.stop_speaking()  # Ensure cleanup
                self.summary_data["providers"][provider_id]["speech_test"] = "failed"
                self.summary_data["providers"][provider_id][
                    "speech_error"
                ] = "Start timeout"
                return

            # Verify playback is active
            if not provider.is_speaking:
                logger.error("Playback not active after start event")
                provider.stop_speaking()  # Ensure cleanup
                self.summary_data["providers"][provider_id]["speech_test"] = "failed"
                self.summary_data["providers"][provider_id][
                    "speech_error"
                ] = "Not active after start"
                return
            logger.info("✓ Playback is active")

            # Test 2: Stop functionality
            logger.info("Testing stop_speaking...")
            provider.stop_speaking()

            # Wait for stop event with timeout
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=2)
                logger.info("✓ Stop event received")
            except TimeoutError:
                logger.error("Stop event not received within timeout")
                self.summary_data["providers"][provider_id]["speech_test"] = "failed"
                self.summary_data["providers"][provider_id][
                    "speech_error"
                ] = "Stop timeout"
                return

            # Verify playback stopped
            if provider.is_speaking:
                logger.error("Playback still active after stop")
                provider.stop_speaking()  # Try stopping again
                self.summary_data["providers"][provider_id]["speech_test"] = "failed"
                self.summary_data["providers"][provider_id][
                    "speech_error"
                ] = "Still active after stop"
                return
            logger.info("✓ Successfully stopped speaking")

            # Short delay to ensure cleanup
            await asyncio.sleep(0.5)

            # Test 3: Full playback completion
            logger.info("Testing full playback...")
            # Reset all events
            start_event.clear()
            stop_event.clear()
            complete_event.clear()

            success = provider.speak(self.test_text, voice_id)
            if not success:
                logger.error("Failed to start full playback test")
                self.summary_data["providers"][provider_id]["speech_test"] = "failed"
                self.summary_data["providers"][provider_id][
                    "speech_error"
                ] = "Failed to start full playback"
                return

            try:
                # Wait for start
                await asyncio.wait_for(start_event.wait(), timeout=2)
                logger.info("✓ Full playback started")

                # Wait for natural completion
                await asyncio.wait_for(complete_event.wait(), timeout=10)
                logger.info("✓ Full playback completed naturally")

                # Verify complete event was triggered
                if not complete_event.is_set():
                    logger.error("Complete event not set after natural completion")
                    provider.stop_speaking()  # Ensure cleanup
                    self.summary_data["providers"][provider_id][
                        "speech_test"
                    ] = "failed"
                    self.summary_data["providers"][provider_id][
                        "speech_error"
                    ] = "No completion event"
                    return

                # Verify playback is not active
                if provider.is_speaking:
                    logger.error("Playback still active after completion")
                    provider.stop_speaking()  # Ensure cleanup
                    self.summary_data["providers"][provider_id][
                        "speech_test"
                    ] = "failed"
                    self.summary_data["providers"][provider_id][
                        "speech_error"
                    ] = "Still active after completion"
                    return

            except TimeoutError:
                logger.error("Full playback did not complete within timeout")
                provider.stop_speaking()  # Ensure cleanup
                self.summary_data["providers"][provider_id]["speech_test"] = "failed"
                self.summary_data["providers"][provider_id][
                    "speech_error"
                ] = "Completion timeout"
                return

            # Update summary data
            self.summary_data["providers"][provider_id]["speech_test"] = "success"

        except Exception as e:
            logger.error(f"Error testing speech functionality: {e!s}")
            logger.exception(f"Detailed error for {provider_id}:")
            self.summary_data["providers"][provider_id]["speech_test"] = "error"
            self.summary_data["providers"][provider_id]["speech_error"] = str(e)
            # Ensure cleanup on error
            try:
                provider.stop_speaking()
            except Exception as cleanup_error:
                logger.debug(f"Cleanup error: {cleanup_error!s}")
                pass

    async def run_tests(self) -> None:
        """Run all tests."""
        # Print available providers
        logger.info("\nAvailable providers:")
        for provider_id in self.providers:
            logger.info(f"  - {provider_id}")

        if not self.providers:
            logger.warning("\nNo providers were initialized!")
            logger.warning("Check the logs for initialization errors.")
            return

        # Test voice reporting
        await self.test_voice_reporting()

        # Test speech functionality for each provider
        for provider_id, provider in self.providers.items():
            try:
                # Get first available voice for the provider
                voices = provider.get_voices()
                if voices:
                    voice_id = voices[0]["id"]
                    await self.test_speech_functionality(provider_id, voice_id)
                else:
                    logger.warning(f"\nNo voices available for {provider_id}")
                    self.summary_data["providers"][provider_id][
                        "speech_test"
                    ] = "no_voices"
            except Exception as e:
                logger.error(f"\nError testing {provider_id}: {e}")
                logger.exception(f"Detailed error for {provider_id}:")
                self.summary_data["providers"][provider_id]["speech_test"] = "error"
                self.summary_data["providers"][provider_id]["speech_error"] = str(e)

        # Log summary
        log_summary("\n=== TTS Engine Test Summary ===")
        log_summary(f"Test completed at: {self.summary_data['timestamp']}\n")

        for provider_id, data in self.summary_data["providers"].items():
            log_summary(f"\n{provider_id}:")
            if data["status"] == "success":
                log_summary("  ✓ Successfully initialized")
                log_summary(f"  ✓ Found {data['voice_count']} voices")
                if "speech_test" in data:
                    log_summary(f"  ✓ Speech test: {data['speech_test'].title()}")
                    if data["speech_test"] == "error":
                        log_summary(f"  ✗ Speech error: {data['speech_error']}")
            else:
                log_summary(f"  ✗ Error: {data['error']}")

        # Save detailed summary to JSON
        with open("test_summary.json", "w") as f:
            json.dump(self.summary_data, f, indent=2)


def test_provider(provider: TTSProviderAbstract, provider_name: str) -> bool:
    """Test a TTS provider.

    Args:
        provider: Provider instance to test
        provider_name: Name of the provider for logging

    Returns:
        True if all tests passed
    """
    try:
        logger.info(f"\n=== Testing {provider_name} ===")

        # Test 1: Get voices
        logger.info("Getting available voices...")
        voices = provider.get_voices()
        if not voices:
            logger.error(f"No voices available for {provider_name}")
            return False
        logger.info(f"Found {len(voices)} voices")
        for voice in voices:
            logger.info(f"Voice: {voice['name']} ({voice['id']})")

        # Test 2: Generate speech data
        logger.info("\nGenerating speech data...")
        audio_data = provider.get_speak_data(TEST_TEXT, voices[0]["id"])
        if audio_data is None:
            logger.error(f"Failed to generate speech data for {provider_name}")
            return False
        logger.info(f"Generated {len(audio_data)} bytes of audio data")

        # Test 3: Play audio
        logger.info("\nPlaying audio...")
        success = audio_manager.play_audio(
            audio_data,
            on_complete=lambda: logger.info(f"{provider_name} playback completed"),
            on_error=lambda e: logger.error(f"{provider_name} playback error: {e}"),
        )
        if not success:
            logger.error(f"Failed to start playback for {provider_name}")
            return False

        # Wait for completion
        while audio_manager.is_playing:
            time.sleep(0.1)
        time.sleep(1)

        logger.info(f"\n{provider_name} tests completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error testing {provider_name}: {e}", exc_info=True)
        return False
    finally:
        # Ensure cleanup
        audio_manager.stop()


def main() -> None:
    """Main entry point."""
    tester = EngineTester()
    asyncio.run(tester.run_tests())


if __name__ == "__main__":
    main()
