"""Speech manager for handling TTS providers."""

import logging
from typing import Any
import time

from tts_wrapper import (
    ElevenLabsClient,
    ElevenLabsTTS,
    GoogleClient,
    GoogleTransClient,
    GoogleTransTTS,
    GoogleTTS,
    MicrosoftClient,
    MicrosoftTTS,
    PlayHTClient,
    PlayHTTTS,
    PollyClient,
    PollyTTS,
    SherpaOnnxClient,
    SherpaOnnxTTS,
    WatsonClient,
    WatsonTTS,
    WitAiClient,
    WitAiTTS,
    eSpeakClient,
    eSpeakTTS,
)

from .base_provider import CustomTTSProvider
from .custom_providers import OpenAITTSProvider


class TTSProvider(CustomTTSProvider):
    """Base class for TTS wrapper providers."""

    def __init__(self):
        """Initialize the provider."""
        super().__init__()
        self.tts = None
        self.timings = []

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        voices = self.tts.get_voices()
        cleaned_voices = []
        for voice in voices:
            language_codes = voice.get("language_codes", [""])
            language = language_codes[0] if language_codes else ""
            cleaned_voices.append(
                {
                    "id": voice.get("id", ""),
                    "name": voice.get("name", ""),
                    "language": language,
                    "language_codes": voice.get("language_codes", []),
                    "gender": voice.get("gender", "Unknown"),
                }
            )
        return cleaned_voices

    def speak(self, text: str, voice_id: str) -> None:
        """Speak text using specified voice."""
        try:
            # First try direct speak
            self.tts.speak(text, voice_id=voice_id)
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")

    def get_speak_data(self, text: str, voice_id: str) -> bytes:
        """Get WAV audio data for text."""
        try:
            import os
            import tempfile

            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Synthesize to WAV file
                self.tts.synth_to_file(text, temp_path, voice_id=voice_id)

                # Read the WAV file
                with open(temp_path, "rb") as f:
                    wav_data = f.read()

                return wav_data
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    self.logger.debug(f"Error cleaning up temp file: {e}")

        except Exception as e:
            self.logger.error(f"Error getting speech data: {e}")
            return b""

    def stop_speaking(self) -> None:
        """Stop current speech playback."""
        try:
            self.tts.stop_speaking()
        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")


class SpeechManager:
    """Manages TTS providers and speech operations."""

    def __init__(self):
        """Initialize the speech manager."""
        self.providers: dict[str, CustomTTSProvider] = {}
        self.current_provider: CustomTTSProvider | None = None
        self.logger = logging.getLogger(__name__)
        self._voices_cache = None
        self._voices_cache_timestamp = 0
        self._voices_cache_ttl = 300  # Cache TTL in seconds (5 minutes)
        self.is_speaking = False

    def _is_voices_cache_valid(self) -> bool:
        """Check if the voices cache is still valid."""
        if self._voices_cache is None:
            return False
        current_time = time.time()
        return (current_time - self._voices_cache_timestamp) < self._voices_cache_ttl

    def init_providers(self, config: dict[str, Any]) -> None:
        """Initialize TTS providers from config."""
        self.providers = {}
        self.current_provider = None

        # Get list of engines from config
        engines = config.get("engines", [])
        if not engines:
            self.logger.warning("No TTS engines specified in config")
            return

        # Initialize each provider
        for engine in engines:
            provider = None
            try:
                self.logger.debug(f"Initializing provider for engine: {engine}")
                if engine == "sherpaonnx":
                    # Initialize Sherpa-ONNX provider
                    engine_config = config.get("engine_configs", {}).get(
                        "sherpaonnx", {}
                    )
                    self.logger.debug(f"Sherpa config: {engine_config}")
                    client = SherpaOnnxClient(
                        model_path=engine_config.get("model_path"),
                        tokens_path=engine_config.get("tokens_path"),
                    )
                    provider = TTSProvider()
                    provider.tts = SherpaOnnxTTS(client)

                elif engine == "microsoft":
                    # Initialize Microsoft Azure provider
                    engine_config = config.get("engine_configs", {}).get(
                        "microsoft", {}
                    )
                    self.logger.debug(f"Microsoft config: {engine_config}")
                    credentials = engine_config.get("credentials", ("", ""))
                    client = MicrosoftClient(credentials=credentials)
                    provider = TTSProvider()
                    provider.tts = MicrosoftTTS(client)

                elif engine == "google":
                    # Initialize Google Cloud provider
                    engine_config = config.get("engine_configs", {}).get("google", {})
                    credentials = engine_config.get("credentials", {})
                    if not credentials:
                        self.logger.warning("Google Cloud credentials not provided")
                        continue
                    client = GoogleClient(credentials=credentials)
                    provider = TTSProvider()
                    provider.tts = GoogleTTS(client)

                elif engine == "googletrans":
                    # Initialize Google Translate provider
                    engine_config = config.get("engine_configs", {}).get(
                        "googletrans", {}
                    )
                    self.logger.debug(f"Google Translate config: {engine_config}")
                    client = GoogleTransClient()
                    provider = TTSProvider()
                    provider.tts = GoogleTransTTS(client)

                elif engine == "elevenlabs":
                    # Initialize ElevenLabs provider
                    engine_config = config.get("engine_configs", {}).get(
                        "elevenlabs", {}
                    )
                    credentials = engine_config.get("credentials", ("",))
                    client = ElevenLabsClient(credentials=credentials)
                    provider = TTSProvider()
                    provider.tts = ElevenLabsTTS(client)

                elif engine == "polly":
                    # Initialize Amazon Polly provider
                    engine_config = config.get("engine_configs", {}).get("polly", {})
                    credentials = engine_config.get("credentials", ("", "", ""))
                    client = PollyClient(credentials=credentials)
                    provider = TTSProvider()
                    provider.tts = PollyTTS(client)

                elif engine == "watson":
                    # Initialize IBM Watson provider
                    engine_config = config.get("engine_configs", {}).get("watson", {})
                    credentials = engine_config.get("credentials", ("", "", ""))
                    client = WatsonClient(credentials=credentials)
                    provider = TTSProvider()
                    provider.tts = WatsonTTS(client)

                elif engine == "witai":
                    # Initialize Wit.ai provider
                    engine_config = config.get("engine_configs", {}).get("witai", {})
                    credentials = engine_config.get("credentials", ("",))
                    client = WitAiClient(credentials=credentials)
                    provider = TTSProvider()
                    provider.tts = WitAiTTS(client)

                elif engine == "playht":
                    # Initialize Play.HT provider
                    engine_config = config.get("engine_configs", {}).get("playht", {})
                    credentials = engine_config.get("credentials", ("", ""))
                    client = PlayHTClient(credentials=credentials)
                    provider = TTSProvider()
                    provider.tts = PlayHTTTS(client)

                elif engine == "espeak":
                    # Initialize eSpeak provider
                    engine_config = config.get("engine_configs", {}).get("espeak", {})
                    client = eSpeakClient()
                    provider = TTSProvider()
                    provider.tts = eSpeakTTS(client)

                elif engine == "openai":
                    # Initialize OpenAI provider
                    engine_config = config.get("engine_configs", {}).get("openai", {})
                    provider = OpenAITTSProvider(engine_config)  # type: ignore

                # Store provider if successfully initialized
                if provider:
                    self.logger.debug(f"Successfully initialized provider for {engine}")
                    self.providers[engine] = provider
                    if not self.current_provider:
                        self.current_provider = provider
                        self.logger.info(
                            f"Current provider: {provider.__class__.__name__}"
                        )
                else:
                    self.logger.warning(f"Failed to initialize provider for {engine}")

            except Exception as e:
                self.logger.error(f"Failed to initialize {engine} provider: {e}")

        if not self.providers:
            self.logger.warning("No TTS providers were successfully initialized")
        else:
            self.logger.debug(f"Initialized providers: {list(self.providers.keys())}")

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices from all providers."""
        # Check cache first
        if self._is_voices_cache_valid():
            self.logger.debug("Returning cached voices")
            return self._voices_cache

        all_voices = []
        for provider_id, provider in self.providers.items():
            try:
                self.logger.info(f"Getting voices from provider: {provider_id}")
                provider_voices = provider.get_voices()
                self.logger.debug(
                    f"Voices from provider {provider_id}: {provider_voices}"
                )

                # Add provider ID and type to each voice
                for voice in provider_voices:
                    # Format name as "Name (Language) - provider"
                    base_name = voice["name"]
                    language = voice.get("language", "")
                    formatted_name = (
                        f"{base_name} ({language}) - {provider_id}"
                        if language
                        else f"{base_name} - {provider_id}"
                    )
                    self.logger.debug(
                        "Formatting voice name: "
                        f"base={base_name}, lang={language}, result={formatted_name}"
                    )

                    voice["name"] = formatted_name
                    voice["providerId"] = provider_id
                    voice["type"] = "VOICE_TYPE_EXTERNAL_DATA"
                    self.logger.debug(f"Final voice entry: {voice}")
                all_voices.extend(provider_voices)
            except Exception as e:
                self.logger.error(f"Error getting voices from {provider_id}: {e}")
                continue

        # Update cache
        self._voices_cache = all_voices
        self._voices_cache_timestamp = time.time()
        return all_voices

    def speak(self, text: str, voice_id: str, provider_id: str | None = None) -> None:
        """Speak text using specified voice."""
        if not text:
            return

        provider: CustomTTSProvider | None = None
        if provider_id and provider_id in self.providers:
            provider = self.providers[provider_id]
        else:
            provider = self.current_provider

        if not provider:
            self.logger.error("No TTS provider available")
            return

        try:
            self.is_speaking = True
            provider.speak(text, voice_id)
            self.is_speaking = False
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")
            self.is_speaking = False

    def get_speak_data(
        self, text: str, voice_id: str, provider_id: str | None = None
    ) -> bytes:
        """Get WAV audio data for text."""
        if not text:
            return b""

        provider: CustomTTSProvider | None = None
        if provider_id and provider_id in self.providers:
            provider = self.providers[provider_id]
        else:
            provider = self.current_provider

        if not provider:
            self.logger.error("No TTS provider available")
            return b""

        try:
            self.is_speaking = True
            data = provider.get_speak_data(text, voice_id)
            self.is_speaking = False
            return data
        except Exception as e:
            self.logger.error(f"Error getting speech data: {e}")
            self.is_speaking = False
            return b""

    def stop_speaking(self) -> None:
        """Stop current speech playback."""
        if self.current_provider:
            try:
                self.current_provider.stop_speaking()
            except Exception as e:
                self.logger.error(f"Error stopping speech: {e}")
            finally:
                self.is_speaking = False


def get_voices(speech_manager: SpeechManager) -> list[dict[str, Any]]:
    """Get available voices."""
    return speech_manager.get_voices()


def get_speak_data(
    text: str,
    voice_id: str,
    provider_id: str | None = None,
    speech_manager: SpeechManager | None = None,
) -> bytes:
    """Get speech data for text."""
    if speech_manager is None:
        raise ValueError("speech_manager is required")
    return speech_manager.get_speak_data(text, voice_id, provider_id)


def speak(
    text: str,
    voice_id: str,
    provider_id: str | None = None,
    speech_manager: SpeechManager | None = None,
) -> None:
    """Speak text using the specified voice."""
    if speech_manager is None:
        raise ValueError("speech_manager is required")
    speech_manager.speak(text, voice_id, provider_id)


def stop_speaking(speech_manager: SpeechManager) -> None:
    """Stop the current speech playback."""
    speech_manager.stop_speaking()


def is_speaking(speech_manager: SpeechManager) -> bool:
    """Check if text is being spoken."""
    return speech_manager.is_speaking
