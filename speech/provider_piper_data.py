import os
import constants
import util

providerId = "piper_data"

def getProviderId():
    return providerId

def getVoiceType():
    return constants.VOICE_TYPE_EXTERNAL_DATA

def getVoices():
    list = []
    # add supported voices
    list.append({"id": "my-voice", "name": "My voice", "lang": "en"})
    return list

def getSpeakData(text, voiceId=None):
    # return byte array of data containing speech
    path = util.getTempFileFullPath(providerId)
    os.system("echo '{}' | piper --model en_US-lessac-medium --output_file {}".format(text, path))
    return util.getTempFileData(providerId)