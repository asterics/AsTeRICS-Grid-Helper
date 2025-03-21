import logging
from typing import Any

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


class TTSProvider:
    """Base class for TTS providers."""

    def __init__(self):
        """Initialize the provider."""
        self.logger = logging.getLogger(__name__)
        self.tts = None

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        raise NotImplementedError

    def get_speak_data(self, text: str, voice_id: str) -> bytes:
        """Get speech data for text using synth_to_bytes."""
        if not hasattr(self.tts, "synth_to_bytes"):
            raise NotImplementedError("Provider does not support audio streaming")
        return self.tts.synth_to_bytes(text, voice_id=voice_id)

    def speak(self, text: str, voice_id: str) -> None:
        """Speak text using the specified voice."""
        if not hasattr(self.tts, "speak"):
            raise NotImplementedError("Provider does not support direct speech")
        self.tts.speak(text, voice_id=voice_id)


class MicrosoftTTSProvider(TTSProvider):
    """Microsoft TTS provider wrapper."""

    def __init__(self, client: MicrosoftClient):
        """Initialize the Microsoft TTS provider."""
        super().__init__()
        self.tts = MicrosoftTTS(client)

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        return self.tts.get_voices()


class SpeechManager:
    """Manages TTS providers and speech operations."""

    def __init__(self):
        """Initialize the speech manager."""
        self.logger = logging.getLogger(__name__)
        self.providers = {}
        self.current_provider = None
        self.is_speaking = False

    def init_providers(self, config=None):
        """Initialize TTS providers based on configuration."""
        if config is None:
            from .config import get_tts_config as get_config

            config = get_config()

        engines = config.get("engines", ["espeak"])
        self.logger.info(f"SpeechManager: Got engines from config: {engines}")

        try:
            for engine in engines:
                engine_name = engine.lower()
                self.logger.info(
                    f"SpeechManager: Attempting to initialize {engine_name} provider..."
                )

                engine_config = config.get("engine_configs", {}).get(engine_name, {})

                if engine_name == "espeak":
                    client = eSpeakClient()
                    self.providers["espeak"] = eSpeakTTS(client)
                elif engine_name == "sherpaonnx":
                    client = SherpaOnnxClient(**engine_config)
                    self.providers["sherpaonnx"] = SherpaOnnxTTS(client)
                elif engine_name == "google":
                    client = GoogleClient(**engine_config)
                    self.providers["google"] = GoogleTTS(client)
                elif engine_name == "googletrans":
                    client = GoogleTransClient(engine_config.get("voice_id", "en-us"))
                    self.providers["googletrans"] = GoogleTransTTS(client)
                elif engine_name == "microsoft":
                    client = MicrosoftClient(**engine_config)
                    self.providers["microsoft"] = MicrosoftTTS(client)
                elif engine_name == "polly":
                    client = PollyClient(**engine_config)
                    self.providers["polly"] = PollyTTS(client)
                elif engine_name == "watson":
                    client = WatsonClient(**engine_config)
                    self.providers["watson"] = WatsonTTS(client)
                elif engine_name == "elevenlabs":
                    client = ElevenLabsClient(**engine_config)
                    self.providers["elevenlabs"] = ElevenLabsTTS(client)
                elif engine_name == "witai":
                    client = WitAiClient(**engine_config)
                    self.providers["witai"] = WitAiTTS(client)
                elif engine_name == "playht":
                    client = PlayHTClient(**engine_config)
                    self.providers["playht"] = PlayHTTTS(client)
                else:
                    self.logger.warning(
                        f"SpeechManager: Unsupported TTS engine: {engine_name}"
                    )
                    continue

            if not self.providers:
                raise ValueError("No valid TTS providers were initialized")

            # Set the first provider as the current provider
            self.current_provider = next(iter(self.providers.values()))
            self.logger.info(
                "SpeechManager: Successfully initialized providers: "
                f"{list(self.providers.keys())}"
            )
            self.logger.info(
                "SpeechManager: Current provider: "
                f"{self.current_provider.__class__.__name__}"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize providers: {e}")
            raise

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices from all providers."""
        all_voices = []
        for provider_id, provider in self.providers.items():
            try:
                self.logger.info(f"Getting voices from provider: {provider_id}")
                voices = provider.get_voices()
                self.logger.info(f"Found {len(voices)} voices from {provider_id}")
                for voice in voices:
                    voice["providerId"] = provider_id
                    voice["type"] = "external_data"
                    voice["name"] = f"{voice['name']}, {provider_id}"
                all_voices.extend(voices)
            except Exception as e:
                self.logger.error(f"Error getting voices from {provider_id}: {e}")
                continue

        self.logger.info(
            f"Found {len(all_voices)} voices across {len(self.providers)} providers"
        )
        return all_voices

    def get_speak_data(
        self, text: str, voice_id: str, provider_id: str | None = None
    ) -> bytes:
        """Get speech data for text using the specified provider."""
        provider = (
            self.providers.get(provider_id) if provider_id else self.current_provider
        )
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")
        import os
        import tempfile

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            # Generate the audio file
            provider.synth_to_file(
                text, temp_file.name, output_format="wav", voice_id=voice_id
            )

            # Read the file contents
            with open(temp_file.name, "rb") as f:
                data = f.read()

            # Clean up the temp file
            os.unlink(temp_file.name)

            return data

    def speak(self, text: str, voice_id: str, provider_id: str | None = None) -> None:
        """Speak text using the specified provider."""
        provider = (
            self.providers.get(provider_id) if provider_id else self.current_provider
        )
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")
        self.is_speaking = True
        try:
            provider.speak(text=text, voice_id=voice_id)
        finally:
            self.is_speaking = False

    def stop_speaking(self) -> None:
        """Stop the current speech playback."""
        if self.current_provider:
            self.current_provider.stop_speaking()
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
