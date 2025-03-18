import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now we can import our modules
from speech.provider_platform_data import provider


def test_voices():
    print("\nTesting getVoices()...")
    voices = provider.getVoices()
    print(f"Found {len(voices)} voices:")
    for voice in voices:
        print(f"- {voice['name']} ({voice['lang']})")
    return True


def test_speak_data():
    print("\nTesting getSpeakData()...")
    # Get the first available voice
    voices = provider.getVoices()
    if not voices:
        print("No voices available!")
        return False

    voice_id = voices[0]["id"]
    print(f"Using voice: {voices[0]['name']}")

    # Get speech data for "hello"
    data = provider.getSpeakData("hello", voice_id)
    print(f"Got {len(data)} bytes of audio data")
    return True


def main():
    print("Starting speech system tests...")

    # Test voice listing
    if not test_voices():
        print("❌ Voice listing test failed!")
        return

    # Test speech data generation
    if not test_speak_data():
        print("❌ Speech data test failed!")
        return

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    main()
