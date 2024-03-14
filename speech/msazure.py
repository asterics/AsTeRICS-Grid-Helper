import azure.cognitiveservices.speech as speechsdk
from credentials import credentials

providerId = "azure"

speech_config = speechsdk.SpeechConfig(credentials["azureKey1"], credentials["azureRegion"])
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

speech_config.speech_synthesis_voice_name='Microsoft Server Speech Text to Speech Voice (zu-ZA, ThembaNeural)'
speech_config.speech_synthesis_voice_name='zu-ZA-ThembaNeural'
speech_config.speech_synthesis_voice_name='en-US-JennyNeural'

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
speaking = False

def getProviderId():
    return providerId

def speak(text, voiceId=None):
    global speaking, speech_synthesizer
    if voiceId:
        speech_config.speech_synthesis_voice_name = voiceId

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speaking = True
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    speaking = False
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")

def isSpeaking():
    return speaking

def stop():
    if speech_synthesizer:
        speech_synthesizer.stop_speaking()

def getVoices():
    list = []
    result = speech_synthesizer.get_voices_async().get()
    voices = result.voices

    for voice in voices:
        list.append({"id": voice.short_name, "name": voice.name, "lang": voice.locale})

    return list


