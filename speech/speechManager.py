import espeak
import msazure

speechProviderList = [msazure]

requiredFns = ["getProviderId", "speak", "isSpeaking", "stop", "getVoices"]
requiredVoiceKeys = ["id", "name"]

speechProviders = {}

def speak(text, providerId, voiceId=None):
    provider = speechProviders[providerId] if providerId in speechProviders else speechProviderList[0]
    provider.speak(text, voiceId)

def isSpeaking():
    for provider in speechProviders.values():
        if provider.isSpeaking():
            return True
    return False

def stop():
    for provider in speechProviders.values():
        provider.stop()

def getVoices():
    allVoices = []
    for provider in speechProviderList:
        voices = provider.getVoices()
        for voice in voices:
            voice["providerId"] = provider.getProviderId()
            allVoices.append(voice)

    return allVoices

def initProviders():
    for provider in speechProviderList:
        id = provider.getProviderId() if hasattr(provider, "getProviderId") else "noProviderId"
        for fnName in requiredFns:
            if not hasattr(provider, fnName):
                raise Exception("ERROR: speech provider '{}' doesn't implement function '{}'!".format(id, fnName))

        voices = provider.getVoices()
        for voice in voices:
            name = voice["id"] or voice["name"] or "noVoiceName"
            for key in requiredVoiceKeys:
                if key not in voice:
                    raise Exception("ERROR: voice '{}' of provider '{}' doesn't have required key '{}'!".format(name, id, key))

        speechProviders[provider.getProviderId()] = provider # store in map

initProviders()