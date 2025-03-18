# AsTeRICS-Grid-Helper
Helper tools to enable [AsTeRICS Grid](https://github.com/asterics/AsTeRICS-Grid) to do actions on the operating system or integrations with external services, which aren't possible within the browser. Currently limited to provide speech from external sources.

## Speech
Normally AsTeRICS Grid uses the [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) and therefore voices that are installed on the operating system (e.g. SAPI voices on Windows, or voices that are coming from a TTS module on Android). Sometimes it's interesting to use voices, which aren't available as system voices. This section describes how to use an external custom speech service using Python.

### Terms
* **Speech provider**: a Python module that implements access to a speech generating service using the [tts_wrapper](https://github.com/willwade/tts-wrapper) library. This library provides unified access to multiple TTS engines:
  * **Online Services**:
    * Microsoft Azure TTS
    * Amazon Polly
    * Google Cloud TTS
    * IBM Watson
    * ElevenLabs
    * Wit.Ai
    * Play.HT
  * **Offline Services**:
    * eSpeak-NG
    * AVSynth (macOS only)
    * SAPI (Windows only)
    * Sherpa-ONNX (supports Piper and other ONNX models)
  * **Experimental**:
    * PicoTTS
    * UWP (WinRT) Speech system (Windows 10+)

  Speech providers can have two types:
   * **type "playing"**: a speech provider where playing the audio file is done internally. Using a speech provider of this type only makes sense, if it's used on the same machine as AsTeRICS Grid.
   * **type "data"**: a speech provider that generates the speech audio data, which then is used by AsTeRICS Grid and played within the browser. This type is preferable, because it makes it possible to run the speech service on any device or server and also allows caching of the data.

### Installation and Usage
#### Speech Service
These steps are necessary to start the speech service that can be used by AsTeRICS Grid:

1. Install Python dependencies:
   ```bash
   pip install flask flask_cors
   ```

2. Install tts_wrapper with the required engines:
   ```bash
   # For all platforms (includes platform-specific engines)
   pip install "py3-tts-wrapper[espeak,avsynth,sapi]"
   
   # For specific platforms:
   # Linux: pip install "py3-tts-wrapper[espeak]"
   # macOS: pip install "py3-tts-wrapper[avsynth]"
   # Windows: pip install "py3-tts-wrapper[sapi]"
   ```

3. Install system dependencies if needed:
   * Linux: 
     ```bash
     sudo apt-get install portaudio19-dev
     sudo apt install espeak-ng  # For eSpeak support
     ```
   * macOS: 
     ```bash
     brew install portaudio
     brew install espeak-ng  # Optional, for eSpeak support
     ```
   * Windows: No additional dependencies needed for SAPI

4. Start the speech service:
   ```bash
   python speech/start.py
   ```

The service will automatically select the appropriate TTS engine based on your platform:
- Linux: eSpeak-NG
- macOS: AVSynth
- Windows: SAPI

#### AsTeRICS Grid
In AsTeRICS Grid do the following steps to use the external speech provider:
* Go to `Settings -> General Settings -> Advanced general settings`
* Configure the `External speech service URL` with the IP/host where the API is running, port `5555`. If the speech service is running on the same computer, use `http://localhost:5555`.
* Reload AsTeRICS Grid (`F5`)
* Go to `Settings -> User settings -> Voice` and enable `Show all voices`
* Verify that the additional voices are selectable and working.

#### Caching
For speech providers with type "data", all generated speech data is automatically cached to the folder `speech/temp`. If you want to cache speech data for a whole AsTeRICS Grid configuration follow these steps:
* configure AsTeRICS Grid to use your desired speech provider / voice (see steps above)
* go to `Settings -> User settings -> Voice -> Advanced voice settings` and click the button `Cache all texts of current configuration using external voice`. This operation may take some time for big AsTeRICS Grid configurations.

### Files
These are the important files within the folder `speech` of this repository:
* `config.py` configuration file where it's possible to define which speech providers should be used
* `provider_<name>_playing.py` implementation of a speech provider which generates speech and plays audio on its own
* `provider_<name>_data.py` implementation of a speech provider which generates speech audio data and returns the binary data, which then is played by AsTeRICS Grid within the browser
* `provider_platform_data.py` platform-specific provider that automatically selects the appropriate TTS engine
* `start.py` main script providing a REST API which can be used by AsTeRICS Grid
* `speechManager.py` script which manages different speech providers and is used to access them by the API defined in `start.py`

### Speech providers
This is a list of predefined speech providers with installation hints:

#### Platform-specific provider
The `platform_data` provider automatically selects the appropriate TTS engine based on your operating system:
* Linux: Uses eSpeak-NG
* macOS: Uses AVSynth
* Windows: Uses SAPI

No additional configuration is needed - it works out of the box on all supported platforms.

#### Other providers
* **msazure_data, msazure_playing**:
   * Requires Azure credentials in `speech/credentials.py`:
     ```python
     AZURE_KEY_1 = "<your-key>"
     AZURE_REGION = "<your-region>"
     ```
   * Get API credentials by [signing up at MS Azure](https://azure.microsoft.com/de-de/get-started/azure-portal) and creating a `SpeechServices` resource.
* **piper_data**: Uses Sherpa-ONNX engine from tts_wrapper to run Piper models. No additional setup required as it uses default model paths.
* **elevenlabs_data**: 
   * Requires ElevenLabs API key in `speech/credentials.py`:
     ```python
     ELEVENLABS_KEY = "<your-key>"
     ```
   * Get API key from [ElevenLabs](https://elevenlabs.io/docs/api-reference/text-to-speech#authentication)

#### Configuration
See [config.py](https://github.com/asterics/AsTeRICS-Grid-Helper/blob/main/speech/config.py), where the speech providers to use can be imported and added to the list `speechProviderList`.

#### Adding new speech providers
Use the templates [provider_template_data.py](https://github.com/asterics/AsTeRICS-Grid-Helper/blob/main/speech/provider_template_data.py) or [provider_template_playing.py](https://github.com/asterics/AsTeRICS-Grid-Helper/blob/main/speech/provider_template_playing.py) depending on which type of speech provider you want to add and implement the predefined methods.

### REST API
The file `speech/start.py` starts the REST API with the following endpoints:
* `/voices` returns a list of voices that are existing within the current configuration.
* `/speak/<text>/<providerId>/<voiceId>` speaks the given text using the given provider and voice.
* `/speakdata/<text>/<providerId>/<voiceId>` returns the binary audio data for the text using the given provider and voice.
* `/cache/<text>/<providerId>/<voiceId>` caches the audio data for the given parameters to a file in `speech/temp` in order to be able to use it faster or without internet connection afterwards.
* `/speaking` returns `true` if the system is currently speaking (only applicable for voice type "speaking")
