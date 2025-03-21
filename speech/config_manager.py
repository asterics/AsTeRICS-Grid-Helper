"""Configuration manager for the speech service."""

import configparser
import json
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Default configuration file path
DEFAULT_CONFIG_PATH = "speech.ini"


@dataclass
class EngineInfo:
    """Information about a TTS engine."""

    name: str
    display_name: str
    description: str
    is_offline: bool
    required_fields: list[str]
    help_text: dict[str, str]


# Define available engines and their properties
AVAILABLE_ENGINES = {
    "sherpaonnx": EngineInfo(
        name="sherpaonnx",
        display_name="Sherpa-ONNX",
        description=(
            "Open-source offline TTS engine using ONNX models "
            "(works with default configuration)"
        ),
        is_offline=True,
        required_fields=[],
        help_text={
            "model_path": "Optional: Path to custom ONNX model file",
            "tokens_path": "Optional: Path to custom tokens file",
        },
    ),
    "openai": EngineInfo(
        name="openai",
        display_name="OpenAI TTS",
        description="OpenAI's GPT-4o mini TTS with high-quality voices",
        is_offline=False,
        required_fields=["api_key"],
        help_text={
            "api_key": "Your OpenAI API key",
            "model": ("Model to use (default: gpt-4o-mini-tts)"),
            "output_format": ("Output format (default: wav)"),
        },
    ),
    "microsoft": EngineInfo(
        name="microsoft",
        display_name="Microsoft Azure",
        description="Microsoft Azure TTS with neural voices",
        is_offline=False,
        required_fields=["subscription_key", "subscription_region"],
        help_text={
            "subscription_key": "Your Azure subscription key",
            "subscription_region": "Azure region (e.g., eastus)",
        },
    ),
    "google": EngineInfo(
        name="google",
        display_name="Google Cloud TTS",
        description="Google Cloud Text-to-Speech",
        is_offline=False,
        required_fields=["credentials_json"],
        help_text={
            "credentials_json": "Your Google Cloud service account JSON credentials",
        },
    ),
    "googletrans": EngineInfo(
        name="googletrans",
        display_name="Google Translate TTS",
        description="Free Google Translate Text-to-Speech (defaults to en-us if no voice specified)",
        is_offline=False,
        required_fields=[],
        help_text={
            "voice_id": "Optional: Voice ID (e.g., en-us, en-uk, fr-fr). Defaults to en-us",
        },
    ),
    "elevenlabs": EngineInfo(
        name="elevenlabs",
        display_name="ElevenLabs",
        description="High-quality AI voices with emotion control",
        is_offline=False,
        required_fields=["api_key"],
        help_text={
            "api_key": "Your ElevenLabs API key",
        },
    ),
    "polly": EngineInfo(
        name="polly",
        display_name="Amazon Polly",
        description="Amazon's Text-to-Speech service",
        is_offline=False,
        required_fields=["aws_region", "aws_key_id", "aws_secret_access_key"],
        help_text={
            "aws_region": "AWS region (e.g., us-east-1)",
            "aws_key_id": "Your AWS access key ID",
            "aws_secret_access_key": "Your AWS secret access key",
        },
    ),
    "watson": EngineInfo(
        name="watson",
        display_name="IBM Watson",
        description="IBM Watson Text-to-Speech",
        is_offline=False,
        required_fields=["api_key", "region", "instance_id", "disable_ssl"],
        help_text={
            "api_key": "Your IBM Watson API key",
            "region": "Service region (e.g., us-east)",
            "instance_id": "Your Watson instance ID",
            "disable_ssl": "Set to true if you have SSL certificate issues",
        },
    ),
    "witai": EngineInfo(
        name="witai",
        display_name="Wit.ai",
        description="Facebook's Wit.ai TTS service",
        is_offline=False,
        required_fields=["token"],
        help_text={
            "token": "Your Wit.ai access token",
        },
    ),
    "playht": EngineInfo(
        name="playht",
        display_name="Play.HT",
        description="Play.HT Text-to-Speech with high-quality voices",
        is_offline=False,
        required_fields=["api_key", "user_id"],
        help_text={
            "api_key": "Your Play.HT API key",
            "user_id": "Your Play.HT user ID",
        },
    ),
    "espeak": EngineInfo(
        name="espeak",
        display_name="eSpeak",
        description="Open-source speech synthesizer",
        is_offline=True,
        required_fields=[],
        help_text={},
    ),
}


class ConfigManager:
    """Manages the speech service configuration."""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self) -> None:
        """Load the configuration from file."""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create a default configuration."""
        self.config["General"] = {
            "engines": "sherpaonnx",
            "cache_enabled": "true",
            "cache_dir": "temp",
        }

        self.config["sherpaonnx"] = {"model_path": "", "tokens_path": ""}

        self.save_config()

    def save_config(self) -> None:
        """Save the configuration to file."""
        with open(self.config_path, "w") as f:
            self.config.write(f)

    def get_enabled_engines(self) -> list[str]:
        """Get the list of enabled engines."""
        engines_str = self.config.get("General", "engines", fallback="sherpaonnx")
        return [e.strip() for e in engines_str.split(",") if e.strip()]

    def set_enabled_engines(self, engines: list[str]) -> None:
        """Set the list of enabled engines."""
        self.config["General"]["engines"] = ",".join(engines)
        self.save_config()

    def get_engine_config(self, engine: str) -> dict[str, str]:
        """Get the configuration for a specific engine."""
        if not self.config.has_section(engine):
            return {}

        config = dict(self.config[engine])
        # Unescape % characters in Google credentials JSON
        if engine == "google" and "credentials_json" in config:
            config["credentials_json"] = config["credentials_json"].replace("%%", "%")

        return config

    def set_engine_config(self, engine: str, config: dict[str, str]) -> None:
        """Set the configuration for a specific engine."""
        if not self.config.has_section(engine):
            self.config.add_section(engine)

        for key, value in config.items():
            # Special handling for Google credentials JSON to avoid interpolation issues
            if engine == "google" and key == "credentials_json":
                # Escape % characters in the JSON string
                if value:
                    value = value.replace("%", "%%")

            self.config[engine][key] = value
        self.save_config()

    def validate_engine_config(self, engine: str) -> list[str]:
        """Validate the configuration for a specific engine.

        Returns:
            List of error messages, empty if configuration is valid
        """
        errors = []
        if engine not in AVAILABLE_ENGINES:
            return [f"Unknown engine: {engine}"]

        engine_info = AVAILABLE_ENGINES[engine]
        engine_config = self.get_engine_config(engine)

        for field in engine_info.required_fields:
            if not engine_config.get(field):
                errors.append(f"Missing required field for {engine}: {field}")

        return errors

    def get_tts_config(self) -> dict:
        """Get the complete TTS configuration."""
        enabled_engines = self.get_enabled_engines()

        config = {
            "engines": enabled_engines,
            "cache_enabled": self.config.getboolean(
                "General", "cache_enabled", fallback=True
            ),
            "cache_dir": self.config.get("General", "cache_dir", fallback="temp"),
            "engine_configs": {},
        }

        for engine in enabled_engines:
            if engine in AVAILABLE_ENGINES:
                engine_config = self.get_engine_config(engine)

                # Format credentials based on engine type
                if engine == "microsoft":
                    config["engine_configs"][engine] = {
                        "credentials": (
                            engine_config.get("subscription_key", ""),
                            engine_config.get("subscription_region", ""),
                        )
                    }
                elif engine == "google":
                    # Handle Google credentials as JSON
                    creds_json = engine_config.get("credentials_json", "{}")
                    try:
                        # Try to parse as JSON first
                        credentials = json.loads(creds_json)
                    except json.JSONDecodeError:
                        # If not JSON, treat as file path
                        if os.path.exists(creds_json):
                            with open(creds_json) as f:
                                credentials = json.load(f)
                        else:
                            credentials = {}
                    config["engine_configs"][engine] = {"credentials": credentials}
                elif engine == "googletrans":
                    config["engine_configs"][engine] = {
                        "voice_id": engine_config.get("voice_id", "en-us")
                    }
                elif engine == "polly":
                    config["engine_configs"][engine] = {
                        "credentials": (
                            engine_config.get("aws_region", ""),
                            engine_config.get("aws_key_id", ""),
                            engine_config.get("aws_secret_access_key", ""),
                        )
                    }
                elif engine == "watson":
                    config["engine_configs"][engine] = {
                        "credentials": (
                            engine_config.get("api_key", ""),
                            engine_config.get("region", ""),
                            engine_config.get("instance_id", ""),
                        ),
                        "disableSSLVerification": engine_config.get(
                            "disable_ssl", ""
                        ).lower()
                        == "true",
                    }
                elif engine == "elevenlabs":
                    config["engine_configs"][engine] = {
                        "credentials": (engine_config.get("api_key", ""),)
                    }
                elif engine == "witai":
                    config["engine_configs"][engine] = {
                        "credentials": (engine_config.get("token", ""),)
                    }
                elif engine == "playht":
                    config["engine_configs"][engine] = {
                        "credentials": (
                            engine_config.get("api_key", ""),
                            engine_config.get("user_id", ""),
                        )
                    }
                else:
                    config["engine_configs"][engine] = engine_config

        return config

    def get_available_engines(self) -> list[EngineInfo]:
        """Get information about all available engines."""
        return list(AVAILABLE_ENGINES.values())

    def get_engine_info(self, engine: str) -> EngineInfo | None:
        """Get information about a specific engine."""
        return AVAILABLE_ENGINES.get(engine)

    def add_engine(self, engine_name: str, engine_config: dict) -> None:
        """Add a new TTS engine to the configuration.

        Args:
            engine_name: The unique identifier for the engine
            engine_config: Dictionary containing engine configuration:
                - display_name: Name to display in UI
                - description: Engine description
                - is_offline: Whether the engine works offline
                - required_fields: List of required configuration fields
        """
        if engine_name in self.config.sections():
            raise ValueError(f"Engine '{engine_name}' already exists")

        # Add the engine section
        self.config[engine_name] = {
            "display_name": engine_config["display_name"],
            "description": engine_config["description"],
            "is_offline": str(engine_config["is_offline"]),
            "required_fields": ",".join(engine_config["required_fields"]),
            "enabled": "false",  # New engines are disabled by default
        }

        # Save the updated configuration
        self.save_config()

    def remove_engine(self, engine_name: str) -> None:
        """Remove a TTS engine from the configuration.

        Args:
            engine_name: The unique identifier for the engine to remove
        """
        if engine_name not in self.config.sections():
            raise ValueError(f"Engine '{engine_name}' does not exist")

        if engine_name == "General":
            raise ValueError("Cannot remove the General section")

        # Remove the engine section
        self.config.remove_section(engine_name)

        # Save the updated configuration
        self.save_config()

    def _get_help_text(self, engine_name: str) -> dict:
        """Get help text for engine configuration fields.

        Args:
            engine_name: The engine identifier

        Returns:
            Dictionary mapping field names to help text
        """
        help_texts = {
            "api_key": "API key for authentication",
            "region": "Service region (e.g., westus, eastus)",
            "voice": "Default voice ID to use",
            "model": "Model name or path",
            "language": "Default language code",
            "rate": "Speech rate (words per minute)",
            "pitch": "Voice pitch (0.0 to 2.0)",
            "volume": "Voice volume (0.0 to 1.0)",
        }

        engine_fields = self.config[engine_name].get("required_fields", "").split(",")
        return {
            field.strip(): help_texts.get(field.strip(), "")
            for field in engine_fields
            if field.strip()
        }
