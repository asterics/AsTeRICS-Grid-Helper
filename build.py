import os
import platform
import subprocess
import sys
from pathlib import Path
import site


def find_package_path(package_name):
    """Find the installation path of a package"""
    for path in site.getsitepackages():
        package_path = os.path.join(path, package_name)
        if os.path.exists(package_path):
            return package_path
    return None


def install_requirements():
    """Install required packages for building"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "flask", "flask_cors"]
    )

    # Install only the platform-specific TTS engine
    current_platform = platform.system().lower()
    if current_platform == "darwin":
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "py3-tts-wrapper[avsynth]"]
        )
    elif current_platform == "windows":
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "py3-tts-wrapper[sapi]"]
        )
    else:  # linux
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "py3-tts-wrapper[espeak]"]
        )


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
            "engine": "avsynth",
        },
        "windows": {
            "name": "asterics-grid-speech.exe",
            "icon": (
                "speech/assets/icon.ico"
                if os.path.exists("speech/assets/icon.ico")
                else None
            ),
            "engine": "sapi",
        },
        "linux": {
            "name": "asterics-grid-speech",
            "icon": (
                "speech/assets/icon.png"
                if os.path.exists("speech/assets/icon.png")
                else None
            ),
            "engine": "espeak",
        },
    }

    options = platform_options.get(
        current_platform,
        {"name": "asterics-grid-speech", "icon": None, "engine": None},
    )

    # Find the tts_wrapper package path
    tts_wrapper_path = find_package_path("tts_wrapper")
    if tts_wrapper_path:
        # Include the entire tts_wrapper package
        data_option = f"{tts_wrapper_path}{os.pathsep}tts_wrapper"

        # Include the specific engine files
        engine_path = os.path.join(tts_wrapper_path, "engines", options["engine"])
        if os.path.exists(engine_path):
            engine_option = (
                f"{engine_path}{os.pathsep}tts_wrapper/engines/{options['engine']}"
            )
    else:
        data_option = None
        engine_option = None

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
    ]

    # Add tts_wrapper package if found
    if data_option:
        cmd.extend(["--add-data", data_option])

    # Add engine files if found
    if engine_option:
        cmd.extend(["--add-data", engine_option])

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
            "--exclude-module",
            "sherpa_onnx",
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

This is a standalone speech service for AsTeRICS Grid.

Usage:
1. Run the executable
2. The service will start automatically on port 5555
3. In AsTeRICS Grid, go to Settings -> General Settings -> Advanced general settings
4. Set the External speech service URL to: http://localhost:5555
5. Reload AsTeRICS Grid (F5)
6. Go to Settings -> User settings -> Voice and enable "Show all voices"

The service will automatically select the appropriate TTS engine for your platform:
- Windows: SAPI (Windows Speech API)
- macOS: AVSynth (macOS Text-to-Speech)
- Linux: eSpeak-NG

Note: The first run may take a few seconds as it initializes the speech engine.
"""
        )


def main():
    """Main build process"""
    print("Installing requirements...")
    install_requirements()

    print("Building executable...")
    build_executable()

    print("\nBuild complete! The executable can be found in the 'dist' directory.")
    print("Please test the executable to ensure it works correctly.")


if __name__ == "__main__":
    main()
