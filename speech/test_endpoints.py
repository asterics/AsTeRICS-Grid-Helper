#!/usr/bin/env python

import time
import unittest
from unittest.mock import patch

from speech.config import get_tts_config
from speech.speech_manager import get_speak_data, get_voices
from speech.start import app


class TestSpeechService(unittest.TestCase):
    """Test cases for the speech service."""

    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True

    def test_voices_endpoint(self):
        """Test the /voices endpoint."""
        response = self.app.get("/voices")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("voices", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "success")
        voices = data["voices"]
        self.assertIsInstance(voices, list)
        if voices:  # If any voices are available
            voice = voices[0]
            self.assertIn("id", voice)
            self.assertIn("name", voice)
            self.assertIn("language_codes", voice)
            self.assertIn("gender", voice)

    def test_voices_endpoint_error(self):
        """Test the /voices endpoint with error handling."""
        with patch("speech.start.get_voices") as mock_get_voices:
            mock_get_voices.side_effect = Exception("Test error")
            response = self.app.get("/voices")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["error"], "Test error")
            self.assertEqual(data["status"], "error")
            self.assertEqual(data["voices"], [])

    def test_speakdata_endpoint(self):
        """Test the /speakdata endpoint."""
        text = "This is a test sentence to verify speech synthesis."
        provider_id = "tts"  # Default provider
        voice_id = "en-US"  # Default voice
        response = self.app.get(f"/speakdata/{text}/{provider_id}/{voice_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/wav")
        # Verify we got some audio data
        self.assertGreater(
            len(response.data), 1000
        )  # Should be at least 1KB of audio data

    def test_speakdata_endpoint_error(self):
        """Test the /speakdata endpoint with error handling."""
        with patch("speech.start.get_speak_data") as mock_get_speak_data:
            mock_get_speak_data.return_value = None
            response = self.app.get("/speakdata/test/tts/en-US")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["error"], "Failed to generate speech data")
            self.assertEqual(data["status"], "error")

    def test_speak_endpoint(self):
        """Test the /speak endpoint."""
        text = "This is a test sentence to verify speech synthesis."
        provider_id = "tts"  # Default provider
        voice_id = "en-US"  # Default voice
        response = self.app.get(f"/speak/{text}/{provider_id}/{voice_id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        # Wait a bit to hear the speech
        time.sleep(2)

    def test_speak_endpoint_error(self):
        """Test the /speak endpoint with error handling."""
        with patch("speech.start.speak") as mock_speak:
            mock_speak.side_effect = Exception("Test error")
            response = self.app.get("/speak/test/tts/en-US")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["error"], "Test error")
            self.assertEqual(data["status"], "error")

    def test_speaking_endpoint(self):
        """Test the /speaking endpoint."""
        response = self.app.get("/speaking/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("speaking", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "success")

    def test_stop_endpoint(self):
        """Test the /stop endpoint."""
        response = self.app.get("/stop/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")

    def test_stop_endpoint_error(self):
        """Test the /stop endpoint with error handling."""
        with patch("speech.start.stop_speaking") as mock_stop:
            mock_stop.side_effect = Exception("Test error")
            response = self.app.get("/stop/")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["error"], "Test error")
            self.assertEqual(data["status"], "error")

    def test_caching(self):
        """Test speech data caching."""
        text = "test"
        provider_id = "tts"  # Default provider
        voice_id = "en-US"  # Default voice
        # First request should generate and cache
        response1 = self.app.get(f"/speakdata/{text}/{provider_id}/{voice_id}")
        self.assertEqual(response1.status_code, 200)
        # Second request should use cache
        response2 = self.app.get(f"/speakdata/{text}/{provider_id}/{voice_id}")
        self.assertEqual(response2.status_code, 200)
        # Verify both responses are identical
        self.assertEqual(response1.data, response2.data)

    def test_config(self):
        """Test TTS configuration."""
        config = get_tts_config()
        self.assertIsInstance(config, dict)
        self.assertIn("engine", config)
        self.assertIn("credentials", config)
        self.assertIn("cache_enabled", config)
        self.assertIn("cache_dir", config)

    def test_core_functionality(self):
        """Test core speech functionality without HTTP."""
        # Test getting voices
        voices = get_voices()
        self.assertIsInstance(voices, list)
        if voices:  # If any voices are available
            voice_id = voices[0]["id"]
            # Test speech data generation
            data = get_speak_data("test", voice_id, "tts")
            self.assertIsInstance(data, bytes)
            self.assertGreater(len(data), 0)

    def test_core_functionality_error(self):
        """Test core speech functionality error handling."""
        with patch("speech.speech_manager.get_voices") as mock_get_voices:
            mock_get_voices.side_effect = Exception("Test error")
            voices = get_voices()
            self.assertEqual(voices, [])

    def test_different_providers(self):
        """Test different TTS providers.

        Note: Most providers require API keys to work. This test only verifies
        that the provider initialization works, not that it can actually generate speech.
        """
        # Test providers that don't require API keys
        local_providers = ["sherpaonnx", "tts"]
        for provider in local_providers:
            with (
                patch("speech.config.get_tts_config") as mock_config,
                patch("speech.speech_manager.speech_manager") as mock_manager,
            ):
                mock_config.return_value = {"engine": provider}
                mock_manager.tts_instance.get_voices.return_value = [
                    {
                        "id": f"{provider}_test_voice",
                        "name": f"Test Voice ({provider})",
                        "language_codes": ["en-US"],
                        "gender": "N",
                    }
                ]
                voices = get_voices()
                self.assertIsInstance(voices, list)
                # Verify we got at least one voice with the expected ID
                voice_ids = [v["id"] for v in voices]
                self.assertIn(f"{provider}_test_voice", voice_ids)

        # Test providers that require API keys (mocked)
        api_providers = [
            "google",
            "microsoft",
            "polly",
            "watson",
            "elevenlabs",
            "witai",
        ]
        for provider in api_providers:
            with (
                patch("speech.config.get_tts_config") as mock_config,
                patch("speech.speech_manager.speech_manager") as mock_manager,
            ):
                mock_config.return_value = {
                    "engine": provider,
                    "credentials": {"api_key": "test_key", "region": "test_region"},
                }
                mock_manager.tts_instance.get_voices.return_value = [
                    {
                        "id": f"{provider}_test_voice",
                        "name": f"Test Voice ({provider})",
                        "language_codes": ["en-US"],
                        "gender": "N",
                    }
                ]
                voices = get_voices()
                self.assertIsInstance(voices, list)
                # Verify we got at least one voice with the expected ID
                voice_ids = [v["id"] for v in voices]
                self.assertIn(f"{provider}_test_voice", voice_ids)


if __name__ == "__main__":
    unittest.main()
