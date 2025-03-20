import logging
from typing import Any

from tts_wrapper import (
    ElevenLabsClient,
    ElevenLabsTTS,
    GoogleClient,
    GoogleTTS,
    MicrosoftClient,
    MicrosoftTTS,
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
    # AVSynthClient,
    # AVSynthTTS,
    # SAPIClient,
    # SAPITTS,
)

from .config import get_tts_config


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
        """Get speech data for text."""
        raise NotImplementedError

    def speak(self, text: str, voice_id: str) -> None:
        """Speak text using the specified voice."""
        raise NotImplementedError


class SpeechManager:
    """Manages TTS providers and speech operations."""

    def __init__(self):
        """Initialize the speech manager."""
        self.logger = logging.getLogger(__name__)
        self.providers = {}
        self.current_provider = None
        self.is_speaking = False

    def init_providers(self):
        """Initialize TTS providers based on configuration."""
        config = get_tts_config()
        engines = config.get("engines", ["espeak"])
        self.logger.info(f"SpeechManager: Got engines from config: {engines}")

        try:
            for engine in engines:
                engine_name = engine.lower()
                self.logger.info(
                    f"SpeechManager: Attempting to initialize {engine_name} provider..."
                )

                if engine_name == "espeak":
                    client = eSpeakClient()
                    self.providers["espeak"] = eSpeakTTS(client)
                    self.logger.info(
                        "SpeechManager: eSpeak provider initialized successfully"
                    )
                elif engine_name == "sherpaonnx" and "sherpaonnx" in config.get(
                    "engine_configs", {}
                ):
                    client = SherpaOnnxClient()
                    self.providers["sherpaonnx"] = SherpaOnnxTTS(client)
                    self.logger.info(
                        "SpeechManager: SherpaOnnx provider initialized successfully"
                    )
                elif engine_name == "google" and "google" in config.get(
                    "engine_configs", {}
                ):
                    client = GoogleClient(credentials=config.get("credentials", {}))
                    self.providers["google"] = GoogleTTS(client)
                    self.logger.info(
                        "SpeechManager: Google provider initialized successfully"
                    )
                elif engine_name == "microsoft" and "microsoft" in config.get(
                    "engine_configs", {}
                ):
                    client = MicrosoftClient(credentials=config.get("credentials", {}))
                    self.providers["microsoft"] = MicrosoftTTS(client)
                    self.logger.info(
                        "SpeechManager: Microsoft provider initialized successfully"
                    )
                elif engine_name == "polly" and "polly" in config.get(
                    "engine_configs", {}
                ):
                    client = PollyClient(credentials=config.get("credentials", {}))
                    self.providers["polly"] = PollyTTS(client)
                    self.logger.info(
                        "SpeechManager: Polly provider initialized successfully"
                    )
                elif engine_name == "watson" and "watson" in config.get(
                    "engine_configs", {}
                ):
                    client = WatsonClient(credentials=config.get("credentials", {}))
                    self.providers["watson"] = WatsonTTS(client)
                    self.logger.info(
                        "SpeechManager: Watson provider initialized successfully"
                    )
                elif engine_name == "elevenlabs" and "elevenlabs" in config.get(
                    "engine_configs", {}
                ):
                    client = ElevenLabsClient(credentials=config.get("credentials", {}))
                    self.providers["elevenlabs"] = ElevenLabsTTS(client)
                    self.logger.info(
                        "SpeechManager: ElevenLabs provider initialized successfully"
                    )
                elif engine_name == "witai" and "witai" in config.get(
                    "engine_configs", {}
                ):
                    client = WitAiClient(credentials=config.get("credentials", {}))
                    self.providers["witai"] = WitAiTTS(client)
                    self.logger.info(
                        "SpeechManager: Wit.AI provider initialized successfully"
                    )
                # elif engine_name == "avsynth" and "avsynth" in config.get(
                #     "engine_configs", {}
                # ):
                #     client = AVSynthClient()
                #     self.providers["avsynth"] = AVSynthTTS(client)
                #     self.logger.info(
                #         "SpeechManager: AVSynth provider initialized successfully"
                #     )
                # elif engine_name == "sapi" and "sapi" in config.get(
                #     "engine_configs", {}
                # ):
                #     client = SAPIClient()
                #     self.providers["sapi"] = SAPITTS(client)
                #     self.logger.info(
                #         "SpeechManager: SAPI provider initialized successfully"
                #     )
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
                f"SpeechManager: Successfully initialized providers: {list(self.providers.keys())}"
            )
            self.logger.info(
                f"SpeechManager: Current provider: {self.current_provider.__class__.__name__}"
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
        return provider.get_speak_data(text, voice_id)

    def speak(self, text: str, voice_id: str, provider_id: str | None = None) -> None:
        """Speak text using the specified provider."""
        provider = (
            self.providers.get(provider_id) if provider_id else self.current_provider
        )
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")
        self.is_speaking = True
        try:
            provider.speak(text, voice_id)
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
