import os
from urllib.parse import quote

def getTempFilename(providerId):
    providerId = getSafeString(providerId)
    return "temp_{}.wav".format(providerId)

def getTempFileFullPath(providerId):
    providerId = getSafeString(providerId)
    currentDir = os.path.dirname(__file__)
    dirname = os.path.join(currentDir, "temp")
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    return os.path.join(dirname, getTempFilename(providerId))

def getCacheFileFullPath(text, providerId, voiceId):
    providerId = getSafeString(providerId)
    text = quote(text)
    voiceId = getSafeString(str(voiceId))
    currentDir = os.path.dirname(__file__)
    dirname = os.path.join(currentDir, "temp", providerId, voiceId)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return os.path.join(dirname, "{}.wav".format(text))

def getTempFileData(providerId):
    path = getTempFileFullPath(providerId)
    in_file = open(path, "rb") # opening for [r]eading as [b]inary
    data = in_file.read()
    in_file.close()
    return data

def saveCacheData(text, providerId, voiceId, data):
    path = getCacheFileFullPath(text, providerId, voiceId)
    out_file = open(path, "wb") # opening for [r]eading as [b]inary
    out_file.write(data)
    out_file.close()

def getCacheData(text, providerId, voiceId):
    data = None
    path = getCacheFileFullPath(text, providerId, voiceId)
    if os.path.isfile(path):
        in_file = open(path, "rb") # opening for [r]eading as [b]inary
        data = in_file.read()
        in_file.close()
    return data

def getSafeString(string):
    keepcharacters = (' ','.','_', '-')
    return "".join(c for c in string if c.isalnum() or c in keepcharacters).rstrip()
