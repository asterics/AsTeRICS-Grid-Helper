#!/usr/bin/env python

import time
import unittest
from unittest.mock import patch

import pytest

from speech.config import get_tts_config
from speech.speech_manager import (
    SpeechManager,
    get_speak_data,
    get_voices,
)
from speech.start import app


@pytest.fixture
def test_app():
    """Create a test Flask app instance."""
    app.config["TESTING"] = True
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the Flask app."""
    return test_app.test_client()


@pytest.fixture(autouse=True)
def setup_speech_manager(mocker):
    """Set up the speech manager for all tests."""
    # Mock the get_tts_config function
    mocker.patch(
        "speech.config.get_tts_config",
        return_value={
            "engines": ["sherpaonnx"],
            "credentials": {},
            "cache_enabled": True,
            "cache_dir": "cache",
            "engine_configs": {"sherpaonnx": {}},
        },
    )

    # Mock the environment variables
    mocker.patch.dict(
        "os.environ",
        {
            "TTS_ENGINE": "sherpaonnx",
            "CACHE_ENABLED": "true",
            "CACHE_DIR": "cache",
        },
    )

    # Create a real speech manager instance
    speech_manager = SpeechManager()
    speech_manager.init_providers()

    # Mock the provider methods that are missing
    if speech_manager.current_provider:
        speech_manager.current_provider.get_speak_data = mocker.Mock(
            return_value=b"test_audio_data"
        )
        speech_manager.current_provider.stop_speaking = mocker.Mock()
        speech_manager.current_provider.get_voices = mocker.Mock(
            return_value=[
                {
                    "id": "en",
                    "name": "English",
                    "language_codes": ["en"],
                    "gender": "N",
                    "providerId": "sherpaonnx",
                    "type": "external_data",
                }
            ]
        )

    # Mock the speech_manager in start.py
    mocker.patch("speech.start.speech_manager", speech_manager)

    return speech_manager


@pytest.fixture
def mock_speech_manager(mocker):
    """Create a mock speech manager."""
    mock_manager = mocker.Mock(spec=SpeechManager)
    mock_manager.get_voices.return_value = [
        {
            "id": "en",
            "name": "English",
            "language_codes": ["en"],
            "gender": "N",
            "providerId": "sherpaonnx",
            "type": "external_data",
        }
    ]
    mock_manager.is_speaking = False
    mock_manager.stop_speaking = mocker.Mock()
    mock_manager.get_speak_data = mocker.Mock(return_value=b"test_audio_data")
    return mock_manager


def test_root_endpoint(test_client):
    """Test the root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "AsTeRICS Grid Speech API"
    assert data["version"] == "1.0"
    assert "endpoints" in data


def test_voices_endpoint(test_client, mock_speech_manager, mocker):
    """Test the voices endpoint."""
    # Mock the get_voices function to use our mock manager
    mocker.patch(
        "speech.start.get_voices", return_value=mock_speech_manager.get_voices()
    )

    response = test_client.get("/voices")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert len(data["voices"]) == 1
    assert data["voices"][0]["id"] == "en"


def test_speak_endpoint(test_client, mock_speech_manager, mocker):
    """Test the speak endpoint."""
    # Mock the speak function to use our mock manager
    mocker.patch("speech.start.speak")

    response = test_client.get("/speak/test_text/sherpaonnx/en")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"


def test_speakdata_endpoint(test_client, mock_speech_manager, mocker):
    """Test the speakdata endpoint."""
    # Mock the get_speak_data function to return test audio data
    mocker.patch("speech.start.get_speak_data", return_value=b"test_audio_data")

    response = test_client.get("/speakdata/test_text/sherpaonnx/en")
    assert response.status_code == 200
    assert response.mimetype == "audio/wav"


def test_speaking_endpoint(test_client, mock_speech_manager, mocker):
    """Test the speaking endpoint."""
    # Mock the is_speaking function to use our mock manager
    mocker.patch("speech.start.is_speaking", return_value=False)

    response = test_client.get("/speaking")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["speaking"] is False


def test_stop_endpoint(test_client, mock_speech_manager, mocker):
    """Test the stop endpoint."""
    # Mock the stop_speaking function to use our mock manager
    mocker.patch("speech.start.stop_speaking")

    response = test_client.get("/stop")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"


def test_cache_endpoint(test_client, mock_speech_manager, mocker):
    """Test the cache endpoint."""
    # Mock the get_speak_data function to return test audio data
    mocker.patch("speech.start.get_speak_data", return_value=b"test_audio_data")

    response = test_client.get("/cache/test_text/espeak/test_voice")
    assert response.status_code == 200
    assert response.get_json() is True


def test_error_handling(test_client, mock_speech_manager, mocker):
    """Test error handling in endpoints."""
    # Mock the get_voices function to raise an exception
    mocker.patch("speech.start.get_voices", side_effect=Exception("Test error"))

    response = test_client.get("/voices")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "error"
    assert "Test error" in data["error"]


class TestSpeechService(unittest.TestCase):
    """Test cases for the speech service."""

    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True
        self.speech_manager = SpeechManager()

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
        provider_id = "sherpaonnx"  # Use sherpaonnx provider
        voice_id = "en"  # Use English voice
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
        provider_id = "sherpaonnx"  # Use sherpaonnx provider
        voice_id = "en"  # Use English voice
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
        response = self.app.get("/speaking")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("speaking", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "success")

    def test_stop_endpoint(self):
        """Test the /stop endpoint."""
        response = self.app.get("/stop")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")

    def test_stop_endpoint_error(self):
        """Test the /stop endpoint with error handling."""
        with patch("speech.start.stop_speaking") as mock_stop:
            mock_stop.side_effect = Exception("Test error")
            response = self.app.get("/stop")
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
        self.assertIn("engines", config)
        self.assertIn("credentials", config)
        self.assertIn("cache_enabled", config)
        self.assertIn("cache_dir", config)
        self.assertIn("engine_configs", config)

    def test_core_functionality(self):
        """Test core speech functionality without HTTP."""
        # Test getting voices
        voices = get_voices(self.speech_manager)
        self.assertIsInstance(voices, list)
        if voices:  # If any voices are available
            voice_id = voices[0]["id"]
            # Test speech data generation
            data = get_speak_data("test", voice_id, "espeak", self.speech_manager)
            self.assertIsInstance(data, bytes)
            self.assertGreater(len(data), 0)

    def test_core_functionality_error(self):
        """Test core speech functionality error handling."""
        with patch("speech.speech_manager.get_voices") as mock_get_voices:
            mock_get_voices.side_effect = Exception("Test error")
            voices = get_voices(self.speech_manager)
            self.assertEqual(voices, [])

    def test_different_providers(self):
        """Test different TTS providers.

        Note: Most providers require API keys to work. This test only verifies
        that the provider initialization works, not that it can actually generate speech.
        """

        # Test providers that don't require API keys
        local_providers = [
            "sherpaonnx"
        ]  # Only test sherpaonnx since it's the only one configured
        for provider in local_providers:
            # Reset the speech manager before each test
            self.speech_manager.providers = {}
            self.speech_manager.current_provider = None

            with patch("speech.config.get_tts_config") as mock_config:
                mock_config.return_value = {
                    "engines": [provider],
                    "credentials": {},
                    "cache_enabled": True,
                    "cache_dir": "cache",
                    "engine_configs": {provider: {}},
                }

                # Force reinitialization of providers
                self.speech_manager.init_providers()

                voices = get_voices(self.speech_manager)
                self.assertIsInstance(voices, list)
                self.assertGreater(len(voices), 0)

                # Get voices from the current provider only
                provider_voices = [v for v in voices if v["providerId"] == provider]
                self.assertGreater(
                    len(provider_voices), 0, f"No voices found for provider {provider}"
                )

                # Verify each voice has the required fields
                for voice in provider_voices:
                    self.assertIn("id", voice)
                    self.assertIn("name", voice)
                    self.assertIn("language_codes", voice)
                    self.assertIn("gender", voice)
                    self.assertIn("providerId", voice)
                    self.assertIn("type", voice)
                    # Verify the provider ID is set correctly
                    self.assertEqual(voice["providerId"], provider)
                    # Verify the voice name includes the provider
                    self.assertIn(provider, voice["name"])

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
            # Reset the speech manager before each test
            self.speech_manager.providers = {}
            self.speech_manager.current_provider = None

            with (
                patch("speech.config.get_tts_config") as mock_config,
                patch("speech.speech_manager.get_voices") as mock_get_voices,
            ):
                mock_config.return_value = {
                    "engines": [provider],
                    "credentials": {"api_key": "test_key", "region": "test_region"},
                    "cache_enabled": True,
                    "cache_dir": "cache",
                    "engine_configs": {
                        provider: {
                            "credentials": {
                                "api_key": "test_key",
                                "region": "test_region",
                            }
                        }
                    },
                }
                mock_get_voices.return_value = [
                    {
                        "id": f"{provider}_test_voice",
                        "name": f"Test Voice ({provider})",
                        "language_codes": ["en-US"],
                        "gender": "N",
                        "providerId": provider,
                        "type": "external_data",
                    }
                ]
                voices = get_voices(self.speech_manager)
                self.assertIsInstance(voices, list)
                self.assertEqual(len(voices), 1)
                self.assertEqual(voices[0]["providerId"], provider)
                self.assertEqual(voices[0]["type"], "external_data")
                self.assertEqual(
                    voices[0]["name"], f"Test Voice ({provider}), {provider}"
                )


if __name__ == "__main__":
    unittest.main()
