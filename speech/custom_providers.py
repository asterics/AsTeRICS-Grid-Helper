"""Custom TTS provider implementations."""

from typing import Any

from .base_provider import CustomTTSProvider


class OpenAITTSProvider(CustomTTSProvider):
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
        self.config = config or {}
        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.model = self.config.get("model", "gpt-4o-mini-tts")
        self.output_format = self.config.get("output_format", "wav")

        # Initialize OpenAI client
        from openai import OpenAI

        self.client = OpenAI(api_key=self.api_key)

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available OpenAI voices."""
        return [
            {
                "id": voice,
                "name": voice.capitalize(),
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

    def speak(self, text: str, voice_id: str) -> None:
        """Speak text using OpenAI TTS."""
        try:
            # Generate audio data
            audio_data = self.get_speak_data(text, voice_id)
            if not audio_data:
                raise RuntimeError("Failed to generate audio data")

            # Play audio using system's audio player
            import io

            import sounddevice as sd
            import soundfile as sf

            # Read WAV data into numpy array
            audio_stream = io.BytesIO(audio_data)
            data, samplerate = sf.read(audio_stream)

            # Play audio
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")

    def get_speak_data(self, text: str, voice_id: str) -> bytes:
        """Get WAV audio data for text using OpenAI TTS."""
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
            return b""

    def stop_speaking(self) -> None:
        """Stop current speech playback."""
        import sounddevice as sd

        sd.stop()
