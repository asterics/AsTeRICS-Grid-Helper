import platform
from typing import Any

from .config import get_tts_config

# Platform-specific imports
if platform.system().lower() == "darwin":
    from tts_wrapper import AVSynthClient, AVSynthTTS
elif platform.system().lower() == "win32":
    from tts_wrapper import SAPITTS, SAPIClient
else:
    from tts_wrapper import eSpeakClient, eSpeakTTS

# Common imports for all platforms
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
)


class SpeechManager:
    """Manages speech synthesis and playback."""

    def __init__(self):
        """Initialize the speech manager."""
        self.tts_instance = None
        self._speaking = False
        self._audio_loaded = False

    def on_speech_start(self):
        """Callback for when speech starts."""
        self._speaking = True

    def on_speech_end(self):
        """Callback for when speech ends."""
        self._speaking = False
        self._audio_loaded = False

    def is_speaking(self) -> bool:
        """Check if text is being spoken."""
        return self._speaking

    def stop_speaking(self) -> None:
        """Stop the current speech playback."""
        try:
            if self.tts_instance and self._audio_loaded:
                self.tts_instance.stop_audio()
                self._speaking = False
                self._audio_loaded = False
        except Exception as e:
            print(f"Error stopping speech: {e}")

    def get_platform_tts(self):
        """Get the appropriate TTS instance for the current platform."""
        if platform.system().lower() == "darwin":
            client = AVSynthClient()
            return AVSynthTTS(client)
        elif platform.system().lower() == "win32":
            client = SAPIClient()
            return SAPITTS(client)
        else:
            client = eSpeakClient()
            return eSpeakTTS(client)

    def init_providers(self):
        """Initialize TTS providers based on configuration."""
        config = get_tts_config()
        engine = config.get(
            "engine", "tts"
        ).lower()  # Convert to lowercase for comparison
        print(f"Initializing TTS provider: {engine}")

        try:
            if engine == "google":
                client = GoogleClient()
                self.tts_instance = GoogleTTS(client)
            elif engine == "microsoft":
                client = MicrosoftClient()
                self.tts_instance = MicrosoftTTS(client)
            elif engine == "polly":
                client = PollyClient()
                self.tts_instance = PollyTTS(client)
            elif engine == "watson":
                client = WatsonClient()
                self.tts_instance = WatsonTTS(client)
            elif engine == "elevenlabs":
                client = ElevenLabsClient()
                self.tts_instance = ElevenLabsTTS(client)
            elif engine == "witai":
                client = WitAiClient()
                self.tts_instance = WitAiTTS(client)
            elif engine == "sherpaonnx":
                client = SherpaOnnxClient()
                self.tts_instance = SherpaOnnxTTS(client)
            else:
                print(
                    f"Engine '{engine}' not found, falling back to platform-specific TTS"
                )
                self.tts_instance = self.get_platform_tts()

            if self.tts_instance:
                print(
                    f"Successfully initialized {self.tts_instance.__class__.__name__}"
                )
            else:
                print("Failed to initialize TTS instance")
        except Exception as e:
            print(f"Error initializing TTS provider: {e}")
            import traceback

            traceback.print_exc()
            self.tts_instance = None

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        try:
            if not self.tts_instance:
                print("Initializing TTS providers...")
                self.init_providers()
            if not self.tts_instance:
                print("No TTS instance available after initialization")
                return []
            print(f"Getting voices from {self.tts_instance.__class__.__name__}")
            voices = self.tts_instance.get_voices()
            print(f"Found {len(voices)} voices")
            return voices
        except Exception as e:
            print(f"Error getting voices: {e!s}")
            return []

    def get_speak_data(
        self, text: str, voice_id: str, provider_id: str
    ) -> bytes | None:
        """Get speech data for the given text."""
        try:
            if not self.tts_instance:
                self.init_providers()
            if not self.tts_instance:
                return None

            # Set voice if specified
            if voice_id:
                self.tts_instance.set_voice(voice_id)

            # Generate audio data
            return self.tts_instance.synth_to_bytes(text)
        except Exception as e:
            print(f"Error generating speech data: {e}")
            return None

    def speak(self, text: str, provider_id: str, voice_id: str | None = None) -> None:
        """Speak the given text using the specified voice."""
        try:
            if not self.tts_instance:
                self.init_providers()
            if not self.tts_instance:
                return

            # Set up callbacks for speech state tracking
            self.tts_instance.connect("onStart", self.on_speech_start)
            self.tts_instance.connect("onEnd", self.on_speech_end)

            # Set voice if specified
            if voice_id:
                self.tts_instance.set_voice(voice_id)

            # Generate and play audio
            audio_bytes = self.tts_instance.synth_to_bytes(text)
            self.tts_instance.load_audio(audio_bytes)
            self._audio_loaded = True
            self.tts_instance.play()
        except Exception as e:
            print(f"Error speaking text: {e}")
            self._speaking = False
            self._audio_loaded = False


# Create a singleton instance
speech_manager = SpeechManager()


# Export functions that use the singleton
def get_voices() -> list[dict[str, Any]]:
    """Get available voices."""
    try:
        if not speech_manager.tts_instance:
            print("Initializing TTS providers...")
            speech_manager.init_providers()
        if not speech_manager.tts_instance:
            print("No TTS instance available after initialization")
            return []
        print(f"Getting voices from {speech_manager.tts_instance.__class__.__name__}")
        voices = speech_manager.tts_instance.get_voices()
        print(f"Found {len(voices)} voices")
        return voices
    except Exception as e:
        print(f"Error getting voices: {e!s}")
        return []


def get_speak_data(text: str, voice_id: str, provider_id: str) -> bytes | None:
    """Get speech data for the given text."""
    return speech_manager.get_speak_data(text, voice_id, provider_id)


def speak(text: str, provider_id: str, voice_id: str | None = None) -> None:
    """Speak the given text using the specified voice."""
    speech_manager.speak(text, provider_id, voice_id)


def init_providers():
    """Initialize TTS providers."""
    speech_manager.init_providers()


def is_speaking() -> bool:
    """Check if text is being spoken."""
    return speech_manager.is_speaking()


def stop_speaking() -> None:
    """Stop the current speech playback."""
    speech_manager.stop_speaking()
