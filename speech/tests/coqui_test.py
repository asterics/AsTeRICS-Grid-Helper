import torch
from TTS.api import TTS
import os

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, "trump.wav")
output = os.path.join(dirname, "output_trump.wav")

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

# List available 🐸TTS models
print(TTS().list_models())

# Init TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
# tts = TTS(model_name="tts_models/de/thorsten/tacotron2-DDC", progress_bar=False)
# Run TTS
# tts.tts_to_file(text="Hallo mein Name ist Max. Ich teste nun die Sprachausgabe.", file_path=output)

# Run TTS
# ❗ Since this model is multi-lingual voice cloning model, we must set the target speaker_wav and language
# Text to speech list of amplitude values as output
# wav = tts.tts(text="Hello world!", speaker_wav=filename, language="de")
# Text to speech to a file
tts.tts_to_file(
    text="Hello, and good morning. I am Donald Trump, president of the United States. I want to note that your work at the University of Applied Sciences Technikum Wien is really amazing. Keep on going!",
    speaker_wav=filename,
    language="en",
    file_path=output,
)
