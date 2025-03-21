#!/usr/bin/env python

import subprocess
from pathlib import Path


def build_executable():
    """Build the executable using PyInstaller with the spec file."""
    # Create necessary directories if they don't exist
    Path("speech/temp").mkdir(parents=True, exist_ok=True)
    Path("speech/cache").mkdir(parents=True, exist_ok=True)

    # Run PyInstaller with the spec file
    subprocess.check_call(["uv", "run", "pyinstaller", "asterics-grid-speech.spec"])

    # Create a simple README in the dist directory
    dist_dir = Path("dist")
    readme_path = dist_dir / "README.txt"

    with open(readme_path, "w") as f:
        f.write(
            """AsTeRICS Grid Speech Service
===========================

This is a standalone speech service for AsTeRICS Grid using Sherpa-ONNX for
offline text-to-speech.

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

Note: The first run may take a few seconds as it downloads and initializes
the Sherpa-ONNX model.

Configuration:
You can modify the config.py file in the executable directory to change:
- The TTS provider (sherpaonnx, espeak, etc.)
- Voice settings
- Other service configurations
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
