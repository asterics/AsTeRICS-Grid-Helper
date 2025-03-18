# template for a speech provider returning binary data

import constants
from typing import Optional, List, Dict, Any
from provider_base import BaseProvider


class TemplateDataProvider(BaseProvider):
    def __init__(self):
        # Initialize your TTS client and instance here
        # Example:
        # client = YourTTSClient()
        # tts = YourTTSEngine(client)
        # super().__init__("template_data", constants.VOICE_TYPE_EXTERNAL_DATA, tts)
        raise NotImplementedError("Template provider - implement your TTS client")

    def getSpeakData(self, text: str, voiceId: Optional[str] = None) -> bytes:
        if voiceId:
            self.tts.set_voice(voiceId)
        return self.tts.synth_to_bytes(text)


# Create a singleton instance
provider = TemplateDataProvider()

# Export the interface functions
getProviderId = provider.getProviderId
getVoiceType = provider.getVoiceType
getVoices = provider.getVoices
getSpeakData = provider.getSpeakData
