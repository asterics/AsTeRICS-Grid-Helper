# template for a speech provider that directly plays speech

from constants import constants

providerId = "fill_provider_id"

def getProviderId():
    return providerId

def getVoiceType():
    return constants["VOICE_TYPE_EXTERNAL_PLAYING"]

def getVoices():
    list = []
    # fill list with voices containing dictionary elements with keys ["id", "name", "lang"]
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