# template for a speech provider returning binary data

from constants import constants

providerId = "fill_provider_id"

def getProviderId():
    return providerId

def getVoiceType():
    return constants["VOICE_TYPE_EXTERNAL_DATA"]

def getVoices():
    list = []
    # add supported voices
    list.append({"id": "my-voice", "name": "My voice", "lang": "en"})
    return list

def getSpeakData(text, voiceId=None):
    # return byte array of data containing speech
    return None