import azure.cognitiveservices.speech as speechsdk
from credentials import credentials
from constants import constants

providerId = "azure"

speech_config = speechsdk.SpeechConfig(credentials["azureKey1"], credentials["azureRegion"])
speech_config.speech_synthesis_voice_name='en-US-JennyNeural'
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
speaking = False

def getProviderId():
    return providerId

def getVoiceType():
    return constants["VOICE_TYPE_EXTERNAL_PLAYING"]

def getVoices():
    list = []
    result = speech_synthesizer.get_voices_async().get()
    voices = result.voices

    for voice in voices:
        list.append({"id": voice.name, "name": voice.name + "_playing", "lang": voice.locale})

    return list

def speak(text, voiceId=None):
    global speaking, speech_synthesizer
    if voiceId:
        speech_config.speech_synthesis_voice_name = voiceId

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speaking = True
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    speaking = False
    errorHandling(speech_synthesis_result)

def isSpeaking():
    return speaking

def stop():
    if speech_synthesizer:
        speech_synthesizer.stop_speaking()

def errorHandling(result):
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")