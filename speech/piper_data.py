import os
from constants import constants

providerId = "piper_data"

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
    os.system("echo '{}' | piper --model en_US-lessac-medium --output_file temp.wav".format(text))

    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'temp.wav')
    in_file = open(filename, "rb") # opening for [r]eading as [b]inary
    data = in_file.read()
    in_file.close()
    return data