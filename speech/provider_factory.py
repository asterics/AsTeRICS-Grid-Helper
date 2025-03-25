"""Factory for creating TTS providers."""

import logging
import importlib.util
import os
import tempfile
from typing import Optional, Any

from .tts_provider import TTSProviderAbstract
from .custom_providers import OpenAITTSProvider

# Import TTS wrapper clients
from tts_wrapper import (
    ElevenLabsClient,
    ElevenLabsTTS,
    GoogleClient,
    GoogleTTS,
    GoogleTransClient,
    GoogleTransTTS,
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

logger = logging.getLogger(__name__)


class TTSProviderFactory:
    """Factory for creating TTS provider instances."""

    @staticmethod
    def create_wrapper_provider(tts_instance: Any) -> TTSProviderAbstract:
        """Create a provider that wraps a TTS wrapper instance."""

        class WrappedProvider(TTSProviderAbstract):
            def __init__(self):
                super().__init__()
                self.tts = tts_instance
                self.logger = logging.getLogger(__name__)

            def get_voices(self) -> list[dict[str, Any]]:
                return self.tts.get_voices() if self.tts else []

            def _generate_speak_data(self, text: str, voice_id: str) -> Optional[bytes]:
                try:
                    # Create a temporary WAV file
                    with tempfile.NamedTemporaryFile(
                        suffix=".wav", delete=False
                    ) as temp_file:
                        temp_path = temp_file.name

                    try:
                        # Synthesize to WAV file using TTS wrapper
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
                    return None

        return WrappedProvider()

    @staticmethod
    def create_provider(
        provider_type: str, config: dict[str, Any]
    ) -> Optional[TTSProviderAbstract]:
        """Create a TTS provider instance.

        Args:
            provider_type: Type of provider to create
            config: Provider configuration

        Returns:
            TTSProvider instance or None if creation fails
        """
        try:

            # Get provider-specific config
            provider_config = config.get("engine_configs", {}).get(provider_type, {})

            # Handle custom providers first
            if provider_type == "openai":
                return OpenAITTSProvider(provider_config)

            # Handle TTS wrapper providers
            if provider_type == "microsoft":
                credentials = provider_config.get("credentials", ("", ""))
                client = MicrosoftClient(credentials=credentials)
                return TTSProviderFactory.create_wrapper_provider(MicrosoftTTS(client))

            elif provider_type == "google":
                credentials = provider_config.get("credentials", {})
                client = GoogleClient(credentials=credentials)
                return TTSProviderFactory.create_wrapper_provider(GoogleTTS(client))

            elif provider_type == "googletrans":
                client = GoogleTransClient()
                return TTSProviderFactory.create_wrapper_provider(
                    GoogleTransTTS(client)
                )

            elif provider_type == "elevenlabs":
                credentials = provider_config.get("credentials", ("",))
                client = ElevenLabsClient(credentials=credentials)
                return TTSProviderFactory.create_wrapper_provider(ElevenLabsTTS(client))

            elif provider_type == "polly":
                credentials = provider_config.get("credentials", ("", "", ""))
                client = PollyClient(credentials=credentials)
                return TTSProviderFactory.create_wrapper_provider(PollyTTS(client))

            elif provider_type == "watson":
                credentials = provider_config.get("credentials", ("", "", ""))
                client = WatsonClient(credentials=credentials)
                return TTSProviderFactory.create_wrapper_provider(WatsonTTS(client))

            elif provider_type == "witai":
                credentials = provider_config.get("credentials", ("",))
                client = WitAiClient(credentials=credentials)
                return TTSProviderFactory.create_wrapper_provider(WitAiTTS(client))

            elif provider_type == "playht":
                credentials = provider_config.get("credentials", ("", ""))
                client = PlayHTClient(credentials=credentials)
                return TTSProviderFactory.create_wrapper_provider(PlayHTTTS(client))

            elif provider_type == "sherpaonnx":
                client = SherpaOnnxClient()
                return TTSProviderFactory.create_wrapper_provider(SherpaOnnxTTS(client))

            elif provider_type == "espeak":
                client = eSpeakClient()
                return TTSProviderFactory.create_wrapper_provider(eSpeakTTS(client))

            else:
                logger.error(f"Unknown provider type: {provider_type}")
                return None

        except Exception as e:
            logger.error(f"Error creating provider {provider_type}: {e}")
            return None
