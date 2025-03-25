"""Custom TTS provider implementations."""

import logging
from typing import Any, Optional

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

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available OpenAI voices.

        Returns:
            List of voice dictionaries in standardized format.
        """
        return [
            {
                "id": voice,
                "name": voice.capitalize(),
                "language": "en",
                "language_codes": ["en"],  # OpenAI voices are optimized for English
                "gender": "Unknown",
            }
            for voice in [
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
        ]

    def get_speak_data(self, text: str, voice_id: str) -> Optional[bytes]:
        """Get WAV audio data for text using OpenAI TTS.

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
