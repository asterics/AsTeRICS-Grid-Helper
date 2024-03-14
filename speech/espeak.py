import pyttsx3

engine = pyttsx3.init()
print("espeak " + str(engine.isBusy())) # why True??

def speak(text, voiceId=None):
    stop()
    if voiceId:
        engine.setProperty("voice", voiceID)
    engine.say(text)
    print("run and wait")
    engine.runAndWait()
    #stop()
    print("done")

def isSpeaking():
    print("espeak " + str(engine.isBusy()))
    return engine.isBusy()

def stop():
    engine.stop()

def getVoices():
    list = []
    voices = engine.getProperty('voices')
    for voice in voices:
        list.append({"id": voice.id, "name": voice.name})
        print("Voice:")
        print(" - ID: %s" % voice.id)
        print(" - Name: %s" % voice.name)
        print(" - Languages: %s" % voice.languages)
        print(" - Gender: %s" % voice.gender)
        print(" - Age: %s" % voice.age)

    return list