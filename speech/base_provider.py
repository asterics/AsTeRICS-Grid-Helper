"""Base class for TTS providers."""

import logging
from typing import Any


class CustomTTSProvider:
    """Base class for custom TTS providers."""

    def __init__(self):
        """Initialize the provider."""
        self.logger = logging.getLogger(__name__)

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        return []

    def speak(self, text: str, voice_id: str) -> None:
        """Speak text using specified voice."""
        pass

    def get_speak_data(self, text: str, voice_id: str) -> bytes:
        """Get WAV audio data for text."""
        return b""

    def stop_speaking(self) -> None:
        """Stop current speech playback."""
        pass
