import credentials
import constants
from typing import Optional
from tts_wrapper import MicrosoftTTS, MicrosoftClient
from provider_base import BaseProvider


class AzureDataProvider(BaseProvider):
    def __init__(self):
        client = MicrosoftClient(
            credentials=(credentials.AZURE_KEY_1, credentials.AZURE_REGION)
        )
        tts = MicrosoftTTS(client)
        super().__init__("azure_data", constants.VOICE_TYPE_EXTERNAL_DATA, tts)

    def getSpeakData(self, text: str, voiceId: Optional[str] = None) -> bytes:
        if voiceId:
            self.tts.set_voice(voiceId)
        return self.tts.synth_to_bytes(text)


# Create a singleton instance
provider = AzureDataProvider()

# Export the interface functions
getProviderId = provider.getProviderId
getVoiceType = provider.getVoiceType
getVoices = provider.getVoices
getSpeakData = provider.getSpeakData
