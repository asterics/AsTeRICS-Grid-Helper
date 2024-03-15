# template for a speech provider that directly plays speech

from constants import constants

providerId = "fill_provider_id"

def getProviderId():
    return providerId

def getVoiceType():
    return constants["VOICE_TYPE_EXTERNAL_PLAYING"]

def getVoices():
    list = []
    # add supported voices
    list.append({"id": "my-voice", "name": "My voice", "lang": "en"})
    return list

def speak(text, voiceId=None):
    # directly speak the text with the given voiceId
    return

def isSpeaking():
    # return True if currently speaking
    return False

def stop():
    # stop speaking
    return