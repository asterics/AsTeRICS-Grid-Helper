from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BaseProvider(ABC):
    def __init__(self, provider_id: str, voice_type: str, tts_instance: Any):
        self.provider_id = provider_id
        self.voice_type = voice_type
        self.tts = tts_instance
        self.speaking = False
        self.is_local = False

    def getProviderId(self) -> str:
        return self.provider_id

    def getVoiceType(self) -> str:
        return self.voice_type

    def getVoices(self) -> List[Dict[str, Any]]:
        voices = self.tts.get_voices()
        voice_list: List[Dict[str, Any]] = []
        for voice in voices:
            # Handle different voice formats
            if isinstance(voice, dict):
                # For providers that return a dict with language_codes
                if "language_codes" in voice and isinstance(
                    voice["language_codes"], dict
                ):
                    lang_code = list(voice["language_codes"].keys())[0]
                else:
                    lang_code = voice.get("language", "en")
                voice_id = voice.get("id", "")
                voice_name = voice.get("name", "")
            else:
                # For providers that return a simpler format (like eSpeak)
                lang_code = "en"  # Default to English
                voice_id = str(voice)
                voice_name = str(voice)

            voice_list.append(
                {
                    "id": voice_id,
                    "name": voice_name,
                    "lang": lang_code,
                    "local": self.is_local,
                }
            )
        return voice_list

    @abstractmethod
    def getSpeakData(self, text: str, voiceId: Optional[str] = None) -> bytes:
        pass

    def speak(self, text: str, voiceId: Optional[str] = None) -> None:
        if voiceId:
            self.tts.set_voice(voiceId)
        self.speaking = True
        self.tts.speak(text)
        self.speaking = False

    def isSpeaking(self) -> bool:
        return self.speaking

    def stop(self) -> None:
        self.tts.stop_audio()
