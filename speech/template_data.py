# template for a speech provider returning binary data

from constants import constants

providerId = "fill_provider_id"

def getProviderId():
    return providerId

def getVoiceType():
    return constants["VOICE_TYPE_EXTERNAL_DATA"]

def getVoices():
    list = []
    # fill list with voices containing dictionary elements with keys ["id", "name", "lang"]
    return list

def getSpeakData(text, voiceId=None):
    # return byte array of data containing speech
    return None