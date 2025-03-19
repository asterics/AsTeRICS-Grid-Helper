"""
Configuration for the speech service.
"""

# Default TTS engine to use
TTS_ENGINE = "SherpaOnnx"

# Credentials for cloud services
CREDENTIALS = {
    # AWS Polly
    "AWS_REGION": "us-east-1",  # e.g., us-east-1
    "AWS_KEY_ID": "",  # Your AWS access key ID
    "AWS_SECRET_ACCESS_KEY": "",  # Your AWS secret access key
    # Google Cloud
    "GOOGLE_SA_PATH": "",  # Path to service account JSON file or dict of credentials
    # Microsoft Azure
    "AZURE_KEY": "",  # Your Azure subscription key
    "AZURE_REGION": "",  # e.g., eastus
    # IBM Watson
    "WATSON_API_KEY": "",  # Your Watson API key
    "WATSON_REGION": "",  # e.g., us-east
    "WATSON_INSTANCE_ID": "",  # Your Watson instance ID
    # ElevenLabs
    "ELEVENLABS_KEY": "",  # Your ElevenLabs API key
    # Wit.AI
    "WITAI_TOKEN": "",  # Your Wit.AI token
}

# Caching settings
CACHE_ENABLED = True
CACHE_DIR = "temp"

# SherpaOnnx specific configuration
SHERPA_ONNX_CONFIG = {
    "model_dir": "models/sherpa-onnx",
}

# Watson specific configuration
WATSON_CONFIG = {
    "disableSSLVerification": False,  # Set to True if you have SSL certificate issues
}


def get_tts_config():
    """Get the TTS configuration based on the selected engine."""
    config = {
        "engine": TTS_ENGINE,
        "credentials": CREDENTIALS,
        "cache_enabled": CACHE_ENABLED,
        "cache_dir": CACHE_DIR,
    }

    # Add engine-specific configurations
    if TTS_ENGINE == "SherpaOnnx":
        config["config"] = SHERPA_ONNX_CONFIG
    elif TTS_ENGINE == "watson":
        config["config"] = WATSON_CONFIG
    elif TTS_ENGINE == "polly":
        config["config"] = {
            "region": CREDENTIALS.get("AWS_REGION"),
            "key_id": CREDENTIALS.get("AWS_KEY_ID"),
            "secret_key": CREDENTIALS.get("AWS_SECRET_ACCESS_KEY"),
        }
    elif TTS_ENGINE == "google":
        config["config"] = {
            "credentials": CREDENTIALS.get("GOOGLE_SA_PATH"),
        }
    elif TTS_ENGINE == "microsoft":
        config["config"] = {
            "key": CREDENTIALS.get("AZURE_KEY"),
            "region": CREDENTIALS.get("AZURE_REGION"),
        }
    elif TTS_ENGINE == "elevenlabs":
        config["config"] = {
            "api_key": CREDENTIALS.get("ELEVENLABS_KEY"),
        }
    elif TTS_ENGINE == "witai":
        config["config"] = {
            "token": CREDENTIALS.get("WITAI_TOKEN"),
        }

    return config
