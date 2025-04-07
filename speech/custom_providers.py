"""Custom TTS provider implementations."""

import logging
from typing import Any

from .tts_provider import TTSProviderAbstract


class OpenAITTSProvider(TTSProviderAbstract):
    """OpenAI TTS provider implementation."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the OpenAI provider.

        Args:
            config: Optional configuration dictionary with keys:
                - api_key: OpenAI API key
                - model: Model to use (default: "gpt-4o-mini-tts")
                - output_format: Output format (default: "wav")
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.model = self.config.get("model", "gpt-4o-mini-tts")
        self.output_format = self.config.get("output_format", "wav")

        # Initialize OpenAI client
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install with: uv pip install openai"
            )

        self.client = openai.OpenAI(api_key=self.api_key)

    def get_voices(self, langcodes: str = "bcp47") -> list[dict[str, Any]]:
        """Get available OpenAI voices with specified language code format.

        Args:
            langcodes: Language code format to return. Options are:
                - "bcp47": BCP-47 format (default)
                - "iso639_3": ISO 639-3 format
                - "display": Human-readable display names
                - "all": All formats in a dictionary

        Returns:
            List of voice dictionaries in standardized format.
        """
        voices = [
            "alloy",
            "ash",
            "ballad",
            "coral",
            "echo",
            "fable",
            "onyx",
            "nova",
            "sage",
            "shimmer",
        ]

        # Format language codes based on requested format
        if langcodes == "bcp47":
            return [
                {
                    "id": voice,
                    "name": voice.capitalize(),
                    "language_codes": ["en"],  # OpenAI voices are optimized for English
                    "gender": "Unknown",
                }
                for voice in voices
            ]
        elif langcodes == "iso639_3":
            return [
                {
                    "id": voice,
                    "name": voice.capitalize(),
                    "language_codes": ["eng"],  # ISO 639-3 code for English
                    "gender": "Unknown",
                }
                for voice in voices
            ]
        elif langcodes == "display":
            return [
                {
                    "id": voice,
                    "name": voice.capitalize(),
                    "language_codes": ["English"],  # Human-readable name
                    "gender": "Unknown",
                }
                for voice in voices
            ]
        elif langcodes == "all":
            return [
                {
                    "id": voice,
                    "name": voice.capitalize(),
                    "language_codes": {
                        "en": {"bcp47": "en", "iso639_3": "eng", "display": "English"}
                    },
                    "gender": "Unknown",
                }
                for voice in voices
            ]
        else:
            # Default to BCP-47 format
            return [
                {
                    "id": voice,
                    "name": voice.capitalize(),
                    "language_codes": ["en"],
                    "gender": "Unknown",
                }
                for voice in voices
            ]

    def _generate_speak_data(self, text: str, voice_id: str) -> bytes | None:
        """Generate WAV audio data for text using OpenAI TTS.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use

        Returns:
            Audio data as bytes, or None if synthesis failed
        """
        try:
            # Generate speech
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice_id,
                input=text,
                response_format=self.output_format,
            )

            # Get audio data
            return response.content
        except Exception as e:
            self.logger.error(f"Error getting speech data: {e}")
            return None
