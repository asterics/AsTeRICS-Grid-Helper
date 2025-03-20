"""
Configuration for the speech service.
"""

import logging
import os

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Default TTS engines to use (comma-separated list)
TTS_ENGINE = "sherpaonnx"  # Can be single engine or comma-separated list

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
    """Get the TTS configuration based on the selected engines."""
    # Split the engine string into a list and clean it
    engines = [e.strip() for e in TTS_ENGINE.split(",")]
    logger.info(f"Config: Parsed engines from TTS_ENGINE: {engines}")

    config = {
        "engines": engines,  # List of engines to initialize
        "credentials": CREDENTIALS,
        "cache_enabled": CACHE_ENABLED,
        "cache_dir": CACHE_DIR,
    }
    logger.info(f"Config: Final engines list in config: {config['engines']}")

    # Add engine-specific configurations
    engine_configs = {}
    for engine in engines:
        engine_name = engine.lower()
        if engine_name == "espeak":
            engine_configs[engine_name] = {}  # espeak doesn't need special config
        elif engine_name == "sherpaonnx":
            engine_configs[engine_name] = {
                "model_path": os.getenv("SHERPAONNX_MODEL_PATH"),
                "tokens_path": os.getenv("SHERPAONNX_TOKENS_PATH"),
            }
        elif engine_name == "google":
            engine_configs[engine_name] = {
                "credentials": {
                    "api_key": os.getenv("GOOGLE_API_KEY"),
                }
            }
        elif engine_name == "microsoft":
            engine_configs[engine_name] = {
                "credentials": {
                    "api_key": os.getenv("MICROSOFT_API_KEY"),
                    "region": os.getenv("MICROSOFT_REGION"),
                }
            }
        elif engine_name == "polly":
            engine_configs[engine_name] = {
                "credentials": {
                    "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                    "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                    "region_name": os.getenv("AWS_REGION"),
                }
            }
        elif engine_name == "watson":
            engine_configs[engine_name] = {
                "credentials": {
                    "api_key": os.getenv("WATSON_API_KEY"),
                    "url": os.getenv("WATSON_URL"),
                }
            }
        elif engine_name == "elevenlabs":
            engine_configs[engine_name] = {
                "credentials": {
                    "api_key": os.getenv("ELEVENLABS_API_KEY"),
                }
            }
        elif engine_name == "witai":
            engine_configs[engine_name] = {
                "credentials": {
                    "api_key": os.getenv("WITAI_API_KEY"),
                }
            }
        elif engine_name == "avsynth":
            engine_configs[engine_name] = {
                "script_path": os.getenv("AVSYNTH_SCRIPT_PATH"),
            }
        elif engine_name == "sapi":
            engine_configs[engine_name] = {}  # SAPI doesn't need special config

    config["engine_configs"] = engine_configs
    return config
