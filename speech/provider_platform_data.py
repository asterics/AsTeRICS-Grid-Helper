import platform
import constants
from typing import Optional, Tuple, Any
from provider_base import BaseProvider
import struct


def add_wav_header(audio_data: bytes) -> bytes:
    """Add WAV header to raw audio data."""
    # WAV header parameters
    num_channels = 1  # mono
    sample_width = 2  # 16-bit
    sample_rate = 22050  # standard rate for most TTS engines
    block_align = num_channels * sample_width
    byte_rate = sample_rate * block_align

    # Create WAV header
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",  # ChunkID
        36 + len(audio_data),  # ChunkSize
        b"WAVE",  # Format
        b"fmt ",  # Subchunk1ID
        16,  # Subchunk1Size
        1,  # AudioFormat (1 = PCM)
        num_channels,  # NumChannels
        sample_rate,  # SampleRate
        byte_rate,  # ByteRate
        block_align,  # BlockAlign
        sample_width * 8,  # BitsPerSample
        b"data",  # Subchunk2ID
        len(audio_data),  # Subchunk2Size
    )

    return header + audio_data


def get_platform_tts() -> Tuple[str, Any, Any]:
    """Get the appropriate TTS client and engine for the current platform."""
    system = platform.system().lower()

    if system == "linux":
        from tts_wrapper import eSpeakTTS, eSpeakClient

        client = eSpeakClient()
        tts = eSpeakTTS(client)
        return "platform_data", client, tts
    elif system == "darwin":  # macOS
        from tts_wrapper import AVSynthTTS, AVSynthClient

        client = AVSynthClient()
        tts = AVSynthTTS(client)
        return "platform_data", client, tts
    elif system == "windows":
        from tts_wrapper import SAPITTS, SAPIClient

        client = SAPIClient()
        tts = SAPITTS(client)
        return "platform_data", client, tts
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")


class PlatformDataProvider(BaseProvider):
    def __init__(self):
        provider_id, client, tts = get_platform_tts()
        super().__init__(provider_id, constants.VOICE_TYPE_EXTERNAL_DATA, tts)
        self.is_local = True  # All platform-specific providers are local

    def getSpeakData(self, text: str, voiceId: Optional[str] = None) -> bytes:
        if voiceId:
            self.tts.set_voice(voiceId)
        raw_data = self.tts.synth_to_bytes(text)
        return add_wav_header(raw_data)


# Create a singleton instance
provider = PlatformDataProvider()

# Export the interface functions
getProviderId = provider.getProviderId
getVoiceType = provider.getVoiceType
getVoices = provider.getVoices
getSpeakData = provider.getSpeakData
