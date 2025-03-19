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

2. Install dependencies using `uv`:
```bash
uv pip install -r requirements.txt
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
