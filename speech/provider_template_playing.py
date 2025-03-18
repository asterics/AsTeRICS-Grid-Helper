# template for a speech provider that directly plays speech

import constants
from typing import Optional
from provider_base import BaseProvider


class TemplatePlayingProvider(BaseProvider):
    def __init__(self):
        # Initialize your TTS client and instance here
        # Example:
        # client = YourTTSClient()
        # tts = YourTTSEngine(client)
        # super().__init__("template_playing", constants.VOICE_TYPE_EXTERNAL_PLAYING, tts)
        raise NotImplementedError("Template provider - implement your TTS client")

    def getSpeakData(self, text: str, voiceId: Optional[str] = None) -> bytes:
        # This provider doesn't need to implement getSpeakData
        raise NotImplementedError("This provider only supports playing")


# Create a singleton instance
provider = TemplatePlayingProvider()

# Export the interface functions
getProviderId = provider.getProviderId
getVoiceType = provider.getVoiceType
getVoices = provider.getVoices
speak = provider.speak
isSpeaking = provider.isSpeaking
stop = provider.stop
