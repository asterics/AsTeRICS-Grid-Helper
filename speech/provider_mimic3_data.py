import os
import constants
import util

providerId = "mimic3_data"

def getProviderId():
    return providerId

def getVoiceType():
    return constants.VOICE_TYPE_EXTERNAL_DATA

def getVoices():
    list = []
    # add supported voices
    list.append({"id": "mimic3-voice", "name": "Mimic3 voice", "lang": "en"})
    return list

def getSpeakData(text, voiceId=None):
    # return byte array of data containing speech
    path = util.getTempFileFullPath(providerId)
    os.system('mimic3 --voice en_UK/apope_low "{}" > {}'.format(text, path))
    return util.getTempFileData(providerId)
