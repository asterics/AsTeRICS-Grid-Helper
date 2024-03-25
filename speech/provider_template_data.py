# template for a speech provider returning binary data

import constants

providerId = "fill_provider_id"

def getProviderId():
    return providerId

def getVoiceType():
    return constants.VOICE_TYPE_EXTERNAL_DATA

def getVoices():
    list = []
    # add supported voices
    list.append({"id": "my-voice", "name": "My voice", "lang": "en"}) # optional boolean property "local" to determine of online/offline voice
    return list

def getSpeakData(text, voiceId=None):
    # return byte array of data containing speech
    # if your speech provider stores the speech data to file, you can use something like this:
    # import util at the top
    # path = util.getTempFileFullPath(providerId)
    # os.system("shell command including <text> {} and <output-path> {}".format(text, path))
    # return util.getTempFileData(providerId)
    return None