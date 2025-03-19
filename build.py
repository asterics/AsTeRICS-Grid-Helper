import os
import platform
import subprocess
from pathlib import Path


def build_executable():
    """Build the executable using PyInstaller"""
    # Get the current platform
    current_platform = platform.system().lower()

    # Define platform-specific options
    platform_options = {
        "darwin": {
            "name": "asterics-grid-speech-mac",
            "icon": (
                "speech/assets/icon.icns"
                if os.path.exists("speech/assets/icon.icns")
                else None
            ),
        },
        "windows": {
            "name": "asterics-grid-speech.exe",
            "icon": (
                "speech/assets/icon.ico"
                if os.path.exists("speech/assets/icon.ico")
                else None
            ),
        },
        "linux": {
            "name": "asterics-grid-speech",
            "icon": (
                "speech/assets/icon.png"
                if os.path.exists("speech/assets/icon.png")
                else None
            ),
        },
    }

    options = platform_options.get(
        current_platform,
        {"name": "asterics-grid-speech", "icon": None},
    )

    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--name",
        options["name"],
        "--onefile",
        "--noconsole",  # Hide console window
        "--clean",  # Clean PyInstaller cache
        "--add-data",
        "speech/temp:temp",  # Include temp directory
        "--add-data",
        "speech/cache:cache",  # Include cache directory
    ]

    # Add platform-specific options
    if options["icon"]:
        cmd.extend(["--icon", options["icon"]])

    # Add the main script and exclusions
    cmd.extend(
        [
            # Exclude unnecessary modules and their dependencies
            "--exclude-module",
            "azure",
            "--exclude-module",
            "google",
            "--exclude-module",
            "boto3",
            "--exclude-module",
            "botocore",
            "--exclude-module",
            "wit",
            "--exclude-module",
            "elevenlabs",
            "speech/start.py",
        ]
    )

    # Run PyInstaller
    subprocess.check_call(cmd)

    # Create a simple README in the dist directory
    dist_dir = Path("dist")
    readme_path = dist_dir / "README.txt"

    with open(readme_path, "w") as f:
        f.write(
            """AsTeRICS Grid Speech Service
===========================

This is a standalone speech service for AsTeRICS Grid using Sherpa-ONNX for offline text-to-speech.

Usage:
1. Run the executable
2. The service will start automatically on port 5555
3. In AsTeRICS Grid, go to Settings -> General Settings -> Advanced general settings
4. Set the External speech service URL to: http://localhost:5555
5. Reload AsTeRICS Grid (F5)
6. Go to Settings -> User settings -> Voice and enable "Show all voices"

Available Voices:
- en-us-amy-medium: English (US) - Amy (Medium)
- en-us-amy-low: English (US) - Amy (Low)
- en-us-amy-high: English (US) - Amy (High)
- en-us-ryan-medium: English (US) - Ryan (Medium)
- en-us-ryan-low: English (US) - Ryan (Low)
- en-us-ryan-high: English (US) - Ryan (High)

Note: The first run may take a few seconds as it downloads and initializes the Sherpa-ONNX model.
"""
        )

    # Create a simple config file in the dist directory
    config_path = dist_dir / "config.py"
    with open(config_path, "w") as f:
        f.write(
            """# Default configuration for AsTeRICS Grid Speech Service

# TTS Configuration
TTS_CONFIG = {
    "tts_provider": "sherpa-onnx",  # Default provider
    "cache_enabled": True,
    "cache_dir": "cache",
    "cache_ttl": 3600,  # Cache TTL in seconds
}

# Voice configuration
VOICE_CONFIG = {
    "default_voice": "en-us-amy-medium",
    "fallback_voice": "en-us-ryan-medium"
}

# No credentials needed for Sherpa-ONNX
CREDENTIALS = {}
"""
        )


def main():
    """Main build process"""
    print("Building executable...")
    build_executable()

    print("\nBuild complete! The executable can be found in the 'dist' directory.")
    print("Please test the executable to ensure it works correctly.")


if __name__ == "__main__":
    main()
