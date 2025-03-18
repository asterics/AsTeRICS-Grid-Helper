import constants
from typing import Optional
from tts_wrapper import SherpaOnnxTTS, SherpaOnnxClient
from provider_base import BaseProvider


class PiperDataProvider(BaseProvider):
    def __init__(self):
        client = SherpaOnnxClient(
            model_path=None, tokens_path=None
        )  # Will use default paths
        tts = SherpaOnnxTTS(client)
        super().__init__("piper_data", constants.VOICE_TYPE_EXTERNAL_DATA, tts)

    def getSpeakData(self, text: str, voiceId: Optional[str] = None) -> bytes:
        if voiceId:
            self.tts.set_voice(voiceId)
        return self.tts.synth_to_bytes(text)


# Create a singleton instance
provider = PiperDataProvider()

# Export the interface functions
getProviderId = provider.getProviderId
getVoiceType = provider.getVoiceType
getVoices = provider.getVoices
getSpeakData = provider.getSpeakData
