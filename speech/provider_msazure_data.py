import azure.cognitiveservices.speech as speechsdk
import credentials
import constants

providerId = "azure_data"

speech_config = speechsdk.SpeechConfig(credentials.AZURE_KEY_1, credentials.AZURE_REGION)
speech_config.speech_synthesis_voice_name='en-US-JennyNeural'

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
speaking = False

def getProviderId():
    return providerId

def getVoiceType():
    return constants.VOICE_TYPE_EXTERNAL_DATA

def getVoices():
    list = []
    result = speech_synthesizer.get_voices_async().get()
    voices = result.voices

    for voice in voices:
        list.append({"id": voice.short_name, "name": voice.name, "lang": voice.locale})

    return list

def getSpeakData(text, voiceId=None):
    global speech_synthesizer
    if voiceId:
        speech_config.speech_synthesis_voice_name = voiceId

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    errorHandling(speech_synthesis_result)

    return speech_synthesis_result.audio_data

def errorHandling(result):
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")