import constants
from typing import Optional
from tts_wrapper import eSpeakTTS, eSpeakClient
from provider_base import BaseProvider


class eSpeakDataProvider(BaseProvider):
    def __init__(self):
        client = eSpeakClient()
        tts = eSpeakTTS(client)
        super().__init__("espeak_data", constants.VOICE_TYPE_EXTERNAL_DATA, tts)
        self.is_local = True  # eSpeak is always local

    def getSpeakData(self, text: str, voiceId: Optional[str] = None) -> bytes:
        if voiceId:
            self.tts.set_voice(voiceId)
        return self.tts.synth_to_bytes(text)


# Create a singleton instance
provider = eSpeakDataProvider()

# Export the interface functions
getProviderId = provider.getProviderId
getVoiceType = provider.getVoiceType
getVoices = provider.getVoices
getSpeakData = provider.getSpeakData
