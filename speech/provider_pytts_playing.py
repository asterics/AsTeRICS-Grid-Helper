import pyttsx3
import constants

engine = pyttsx3.init()
speaking = False

def getProviderId():
    return "pytts"

def getVoiceType():
    return constants.VOICE_TYPE_EXTERNAL_PLAYING

def speak(text, voiceId=None):
    global speaking
    stop()
    if speaking:
        return
    if voiceId:
        engine.setProperty("voice", voiceId)
    engine.say(text)
    speaking = True
    # return engine.runAndWait() # hanging in combination with Flask on Windows?!
    engine.startLoop(False)
    engine.iterate()
    engine.endLoop()
    speaking = False

def isSpeaking():
    # return engine.isBusy() # always returns True on Windows?!
    return speaking

def stop():
    engine.stop()

def getVoices():
    list = []
    voices = engine.getProperty('voices')
    for voice in voices:
        list.append({"id": voice.id, "name": voice.name})

    return list