import espeak
import msazure

requiredFns = ["speak", "isSpeaking", "stop", "getVoices"]
speechProviders = {
    # "espeak": espeak,
    "azure": msazure
}

def speak(text, providerId, voiceId=None):
    provider = speechProviders[providerId]
    provider.speak(text, voiceId)

def isSpeaking():
    for provider in speechProviders.values():
        if provider.isSpeaking():
            return True
    return False

def stop():
    for provider in speechProviders.values():
        provider.stop()

def getVoices(providerId):
    provider = speechProviders[providerId]
    return provider.getVoices()

def testProviders():
    for key in speechProviders.keys():
        provider = speechProviders[key]
        for fnName in requiredFns:
            if not hasattr(provider, fnName):
                raise Exception("ERROR: speech provider '{}' doesn't implement function '{}'!".format(key, fnName))

testProviders()