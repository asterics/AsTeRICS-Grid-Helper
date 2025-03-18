import os
from urllib.parse import quote
from typing import Optional


def getTempFilename(providerId: str) -> str:
    providerId = getSafeString(providerId)
    return "temp_{}.wav".format(providerId)


def getTempFileFullPath(providerId: str) -> str:
    providerId = getSafeString(providerId)
    currentDir = os.path.dirname(__file__)
    dirname = os.path.join(currentDir, "temp")
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    return os.path.join(dirname, getTempFilename(providerId))


def getCacheFileFullPath(text: str, providerId: str, voiceId: str) -> str:
    providerId = getSafeString(providerId)
    text = quote(text)
    voiceId = getSafeString(str(voiceId))
    currentDir = os.path.dirname(__file__)
    dirname = os.path.join(currentDir, "temp", providerId, voiceId)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return os.path.join(dirname, "{}.wav".format(text))


def getTempFileData(providerId: str) -> bytes:
    path = getTempFileFullPath(providerId)
    with open(path, "rb") as in_file:
        return in_file.read()


def saveCacheData(text: str, providerId: str, voiceId: str, data: bytes) -> None:
    path = getCacheFileFullPath(text, providerId, voiceId)
    with open(path, "wb") as out_file:
        out_file.write(data)


def getCacheData(text: str, providerId: str, voiceId: str) -> Optional[bytes]:
    path = getCacheFileFullPath(text, providerId, voiceId)
    if os.path.isfile(path):
        with open(path, "rb") as in_file:
            return in_file.read()
    return None


def getSafeString(string: str) -> str:
    keepcharacters = (" ", ".", "_", "-")
    return "".join(c for c in string if c.isalnum() or c in keepcharacters).rstrip()
