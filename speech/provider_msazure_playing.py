import credentials
import constants
from typing import Optional
from tts_wrapper import MicrosoftTTS, MicrosoftClient
from provider_base import BaseProvider


class AzurePlayingProvider(BaseProvider):
    def __init__(self):
        client = MicrosoftClient(
            credentials=(credentials.AZURE_KEY_1, credentials.AZURE_REGION)
        )
        tts = MicrosoftTTS(client)
        super().__init__("azure_playing", constants.VOICE_TYPE_EXTERNAL_PLAYING, tts)

    def getSpeakData(self, text: str, voiceId: Optional[str] = None) -> bytes:
        # This provider doesn't need to implement getSpeakData
        raise NotImplementedError("This provider only supports playing")


# Create a singleton instance
provider = AzurePlayingProvider()

# Export the interface functions
getProviderId = provider.getProviderId
getVoiceType = provider.getVoiceType
getVoices = provider.getVoices
speak = provider.speak
isSpeaking = provider.isSpeaking
stop = provider.stop
