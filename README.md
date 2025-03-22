# AsTeRICS Grid Helper

A text-to-speech service that provides a simple HTTP API for speech synthesis. This service is designed to work with AsTeRICS Grid and supports multiple TTS providers, with Sherpa-ONNX as the default provider.

## Features

- Simple HTTP API for text-to-speech synthesis
- Support for multiple TTS providers:
  - Sherpa-ONNX (default, offline)
  - Amazon Polly
  - Google Cloud TTS
  - OpenAI TTS
  - Google Translate TTS
  - Microsoft Azure TTS
  - IBM Watson
  - ElevenLabs
  - Wit.AI
- Automatic model downloading and caching
- Cross-platform support (Windows, macOS, Linux)
- CORS enabled for web applications
- Voice selection and management
- Audio data streaming

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AsTeRICS-Grid-Helper.git
cd AsTeRICS-Grid-Helper
```

2. Install UV

Follow the instructions at https://docs.astral.sh/uv/getting-started/installation/#installation-methods


## Usage

### Starting the Service

Run the service using:
```bash
uv run python -m speech.start
```

The service will start on `http://localhost:5555` by default.

### Building Executables

To build platform-specific executables:

```bash
uv run python build.py
```

This will create executables in the `dist` directory.

### API Endpoints

#### List Available Voices
```bash
curl http://localhost:5555/apivoices
```

#### Generate Speech Data
```bash
curl "http://localhost:5555/apispeakdata/Hello%20World/en-us-amy-medium" --output output.wav
```

#### Speak Text
```bash
curl "http://localhost:5555/api/speak/Hello%20World/en-us-amy-medium"
```

### Configuration

The service can be configured by modifying `speech.ini`. Here's an example configuration:

```ini
[General]
engines = sherpaonnx,microsoft,google,googletrans,elevenlabs,polly,witai,playht,espeak,openai
cache_enabled = True
cache_dir = temp

[microsoft]
subscription_key = your-subscription-key
subscription_region = your-region

[elevenlabs]
api_key = your-api-key

[polly]
aws_key_id = your-aws-key-id
aws_secret_access_key = your-aws-secret-key
aws_region = your-aws-region

[witai]
token = your-witai-token

[sherpaonnx]
# No additional configuration needed for sherpaonnx

[googletrans]
voice_id = 

[google]
credentials_json = {
    "type": "service_account",
    "project_id": "your-project-id",
    "private_key_id": "your-private-key-id",
    "private_key": "your-private-key",
    "client_email": "your-client-email",
    "client_id": "your-client-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "your-cert-url"
}

[espeak]
# No additional configuration needed for espeak

[playht]
api_key = your-playht-api-key
user_id = your-playht-user-id

[openai]
api_key = your-openai-api-key
model = gpt-4o-mini-tts
output_format = wav
```

You can also configure the service through the web interface at `http://localhost:5555` which provides a user-friendly way to:
1. Enable/disable TTS providers
2. Configure provider credentials
3. Manage cache settings
4. Test different voices


### Using Different TTS Providers

To use a different TTS provider:

1. Add the provider to the `engines` list in the `[General]` section
2. Add the required credentials in the provider's section
3. Restart the service

Example for using Amazon Polly:
```ini
[General]
engines = polly
cache_enabled = True
cache_dir = temp

[polly]
aws_key_id = your-aws-key-id
aws_secret_access_key = your-aws-secret-key
aws_region = us-east-1
```

You can allow multiple providers to be used at the same time.
eg.
```ini
[General]
engines = polly,sherpaonnx
```

## Development

### Creating Custom TTS Providers

The system supports custom TTS providers through a simple interface. This allows you to integrate any TTS engine that can be controlled via command line or API.

### Provider Interface

To create a custom provider, create a new class that inherits from `CustomTTSProvider` in `speech/custom_providers.py`. Here's a complete example:

```python
from typing import Any
from speech.base_provider import CustomTTSProvider

class MyCustomProvider(CustomTTSProvider):
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the provider.
        
        Args:
            config: Configuration dictionary with provider-specific settings
        """
        super().__init__()
        self.config = config or {}
        # Initialize your TTS engine here
        # Example: self.engine = MyTTSEngine(self.config)

    def get_voices(self) -> list[dict[str, Any]]:
        """Return list of available voices.
        
        Returns:
            List of dictionaries with the following keys:
            - id: Unique identifier for the voice
            - name: Display name of the voice
            - language_codes: List of supported language codes
            - gender: Voice gender (M/F/N)
        """
        # Example:
        return [
            {
                "id": "voice1",
                "name": "Voice 1",
                "language_codes": ["en-US"],
                "gender": "F"
            }
        ]

    def speak(self, text: str, voice_id: str) -> None:
        """Speak text using specified voice.
        
        Args:
            text: Text to speak
            voice_id: ID of the voice to use
        """
        # Implement direct speech output
        # Example: self.engine.speak(text, voice_id)

    def get_speak_data(self, text: str, voice_id: str) -> bytes:
        """Get WAV audio data for text.
        
        Args:
            text: Text to convert to speech
            voice_id: ID of the voice to use
            
        Returns:
            WAV format audio data as bytes
        """
        # Example:
        # audio_data = self.engine.synthesize(text, voice_id)
        # return audio_data
        return b""

    def stop_speaking(self) -> None:
        """Stop current speech playback."""
        # Example: self.engine.stop()
        pass
```

### Registering Your Provider

1. Add your provider class to `speech/custom_providers.py`

2. Add an initialization method to `SpeechManager` in `speech/speech_manager.py`:

```python
def init_myprovider_provider(self, config: dict[str, Any]) -> CustomTTSProvider | None:
    """Initialize your custom provider.
    
    Args:
        config: Configuration dictionary with provider-specific settings
        
    Returns:
        Initialized provider instance or None if initialization fails
    """
    try:
        from .custom_providers import MyCustomProvider
        return MyCustomProvider(config)
    except Exception as e:
        self.logger.error(f"Failed to initialize MyProvider: {e}")
        return None
```

3. Add your provider to the `init_providers` method in `SpeechManager`:

```python
def init_providers(self, config: dict[str, Any]) -> None:
    """Initialize TTS providers from config."""
    # ... existing code ...
    
    for engine in engines:
        try:
            if engine == "myprovider":
                provider = self.init_myprovider_provider(config)
                if provider:
                    self.providers[engine] = provider
            # ... other providers ...
```


### Example Implementation: OpenAI TTS Provider

The OpenAI TTS provider demonstrates a complete implementation:

```python
from typing import Any
from speech.base_provider import CustomTTSProvider
from openai import OpenAI

class OpenAITTSProvider(CustomTTSProvider):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__()
        self.config = config or {}
        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        self.model = self.config.get("model", "gpt-4o-mini-tts")
        self.output_format = self.config.get("output_format", "wav")
        self.client = OpenAI(api_key=self.api_key)

    def get_voices(self) -> list[dict[str, Any]]:
        return [
            {
                "id": voice,
                "name": voice.capitalize(),
                "language_codes": ["en"],
                "gender": "Unknown"
            }
            for voice in [
                "alloy", "ash", "ballad", "coral", "echo",
                "fable", "onyx", "nova", "sage", "shimmer"
            ]
        ]

    def speak(self, text: str, voice_id: str) -> None:
        audio_data = self.get_speak_data(text, voice_id)
        if not audio_data:
            raise RuntimeError("Failed to generate audio data")
            
        import io
        import sounddevice as sd
        import soundfile as sf
        
        audio_stream = io.BytesIO(audio_data)
        data, samplerate = sf.read(audio_stream)
        sd.play(data, samplerate)
        sd.wait()

    def get_speak_data(self, text: str, voice_id: str) -> bytes:
        response = self.client.audio.speech.create(
            model=self.model,
            voice=voice_id,
            input=text,
            response_format=self.output_format
        )
        return response.content

    def stop_speaking(self) -> None:
        import sounddevice as sd
        sd.stop()
```

### Testing Your Provider

1. Install your provider's dependencies:
```bash
uv pip install your-provider-dependencies
```

3. Test your provider:
```bash
uv run python -m speech.start
```

4. Use the web interface at `http://localhost:5555` to test your provider's functionality.


### Running Tests

Run the test suite:
```bash
uv run pytest
```

### Project Structure

```
speech/
├── config.py           # Configuration settings
├── speechManager.py    # Core TTS functionality
├── start.py           # Flask server implementation
└── test_endpoints.py  # API endpoint tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
