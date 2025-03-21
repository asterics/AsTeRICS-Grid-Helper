# AsTeRICS Grid Helper

A text-to-speech service that provides a simple HTTP API for speech synthesis. This service is designed to work with AsTeRICS Grid and supports multiple TTS providers, with Sherpa-ONNX as the default provider.

## Features

- Simple HTTP API for text-to-speech synthesis
- Support for multiple TTS providers:
  - Sherpa-ONNX (default, offline)
  - Amazon Polly
  - Google Cloud TTS
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

This will create executables in the `dist` directory:
- macOS: `asterics-grid-speech-mac`
- Windows: `asterics-grid-speech.exe`
- Linux: `asterics-grid-speech`

### API Endpoints

#### List Available Voices
```bash
curl http://localhost:5555/voices
```

#### Generate Speech Data
```bash
curl "http://localhost:5555/speakdata/Hello%20World/en-us-amy-medium" --output output.wav
```

#### Speak Text
```bash
curl "http://localhost:5555/speak/Hello%20World/en-us-amy-medium"
```

### Configuration

The service can be configured by modifying `speech/config.py`. Here's an example configuration:

```python
# TTS Configuration
TTS_CONFIG = {
    "tts_provider": "sherpa-onnx",  # Default provider
    "cache_enabled": True,
    "cache_dir": "cache",
    "cache_ttl": 3600,  # Cache TTL in seconds
}

# Provider-specific credentials
CREDENTIALS = {
    "polly": {
        "aws_access_key_id": "your-access-key",
        "aws_secret_access_key": "your-secret-key",
        "region_name": "us-east-1"
    },
    "google": {
        "credentials_file": "path/to/credentials.json"
    },
    "azure": {
        "subscription_key": "your-key",
        "region": "your-region"
    },
    "watson": {
        "apikey": "your-api-key",
        "url": "your-service-url"
    },
    "elevenlabs": {
        "api_key": "your-api-key"
    },
    "wit": {
        "api_key": "your-api-key"
    }
}

# Voice configuration
VOICE_CONFIG = {
    "default_voice": "en-us-amy-medium",
    "fallback_voice": "en-us-ryan-medium"
}
```

### Available Voices

The service provides several pre-configured voices using the Piper model:

- `en-us-amy-medium`: English (US) - Amy (Medium)
- `en-us-amy-low`: English (US) - Amy (Low)
- `en-us-amy-high`: English (US) - Amy (High)
- `en-us-ryan-medium`: English (US) - Ryan (Medium)
- `en-us-ryan-low`: English (US) - Ryan (Low)
- `en-us-ryan-high`: English (US) - Ryan (High)

### Using Different TTS Providers

To use a different TTS provider:

1. Update the `tts_provider` in `TTS_CONFIG`
2. Add the required credentials in the `CREDENTIALS` section
3. Restart the service

Example for using Amazon Polly:
```python
TTS_CONFIG = {
    "tts_provider": "polly",
    "cache_enabled": True,
    "cache_dir": "cache",
    "cache_ttl": 3600,
}

CREDENTIALS = {
    "polly": {
        "aws_access_key_id": "your-access-key",
        "aws_secret_access_key": "your-secret-key",
        "region_name": "us-east-1"
    }
}
```

## Creating Custom TTS Providers

The system supports custom TTS providers through a simple interface. This allows you to integrate any TTS engine that can be controlled via command line or API.

### Provider Interface

To create a custom provider, create a new class that inherits from `CustomTTSProvider` in `speech/custom_providers.py`:

```python
from speech.speech_manager import CustomTTSProvider

class MyCustomProvider(CustomTTSProvider):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__()
        self.config = config or {}
        # Initialize your TTS engine here

    def get_voices(self) -> list[dict[str, Any]]:
        """Return list of available voices."""
        # Return list of dicts with keys: id, name, language_codes, gender
        return []

    def speak(self, text: str, voice_id: str) -> None:
        """Speak text using specified voice."""
        # Implement direct speech output
        pass

    def get_speak_data(self, text: str, voice_id: str) -> bytes:
        """Get WAV audio data for text."""
        # Return WAV format audio data
        return b""

    def stop_speaking(self) -> None:
        """Stop current speech playback."""
        # Implement stop functionality
        pass
```

### Registering Your Provider

Add an initialization method to `SpeechManager` in `speech/speech_manager.py`:

```python
def init_myprovider_provider(self, config: dict[str, Any]) -> CustomTTSProvider | None:
    """Initialize your custom provider."""
    try:
        from .custom_providers import MyCustomProvider
        return MyCustomProvider(config)
    except Exception as e:
        self.logger.error(f"Failed to initialize MyProvider: {e}")
        return None
```

### Configuration

Add your provider to `speech.ini`:

```ini
[engines]
engines = myprovider,espeak

[engine_configs]
myprovider_path = /path/to/myprovider
myprovider_data_dir = /path/to/data
```

### Example Implementations

#### OpenAI TTS Provider

The OpenAI TTS provider demonstrates integration with OpenAI's text-to-speech API:

```ini
[engines]
engines = openai

[engine_configs]
openai_api_key = your-api-key
openai_model = gpt-4o-mini-tts
openai_output_format = wav
```

Features:
- Uses OpenAI's GPT-4o mini TTS model
- Supports 11 built-in voices (alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer)
- Optimized for English but supports multiple languages
- High-quality, natural-sounding speech
- Streaming support for real-time playback

To use the OpenAI provider:

1. Get an API key from [OpenAI](https://platform.openai.com)
2. Set the `OPENAI_API_KEY` environment variable or add it to your config
3. Select a voice from the available options
4. Use the provider as normal

Example usage:
```python
from speech.speech_manager import SpeechManager
from speech.config import get_tts_config

# Initialize with OpenAI
config = get_tts_config()
config["engines"] = ["openai"]
config["engine_configs"] = {
    "openai": {
        "api_key": "your-api-key",
        "model": "gpt-4o-mini-tts",
        "output_format": "wav"
    }
}

speech_manager = SpeechManager()
speech_manager.init_providers(config)

# Get available voices
voices = speech_manager.get_voices()
for voice in voices:
    print(f"- {voice['name']} ({voice['language_codes'][0]})")

# Speak text
speech_manager.speak("Hello, this is a test.", "alloy")
```

Note: The OpenAI TTS service requires an API key and may incur costs based on usage. See [OpenAI's pricing](https://openai.com/pricing) for details.

#### Template Provider

The `TemplateProvider` class in `speech/custom_providers.py` provides a base template for implementing new TTS providers. It includes:

1. Basic provider structure
2. Required method signatures
3. Type hints and documentation
4. Error handling patterns

Use this template as a starting point for implementing new providers.

## Development

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
