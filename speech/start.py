#!/usr/bin/env python

import os
import sys
from flask import Flask, jsonify, request, make_response, send_file
from flask_cors import CORS
from urllib.parse import unquote
from io import BytesIO
import speechManager
import config

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)


@app.route("/voices/", methods=["GET"])
def voices():
    voices = speechManager.getVoices()
    return jsonify(voices)


@app.route("/speak/<text>/", methods=["POST", "GET"])
@app.route("/speak/<text>/<providerId>/", methods=["POST", "GET"])
@app.route("/speak/<text>/<providerId>/<voiceId>", methods=["POST", "GET"])
def speak_text(text: str, providerId: str = "", voiceId: str = ""):
    text = unquote(text).lower()
    providerId = unquote(providerId)
    voiceId = unquote(voiceId)
    speechManager.speak(text, providerId, voiceId)
    return jsonify(True)


@app.route("/speakdata/<text>/", methods=["POST", "GET"])
@app.route("/speakdata/<text>/<providerId>/", methods=["POST", "GET"])
@app.route("/speakdata/<text>/<providerId>/<voiceId>", methods=["POST", "GET"])
def speakData(text: str, providerId: str = "", voiceId: str = ""):
    text = unquote(text).lower()
    providerId = unquote(providerId)
    voiceId = unquote(voiceId)
    data = speechManager.getSpeakData(text, voiceId, providerId)
    if data:
        return send_file(BytesIO(data), mimetype="audio/wav")
    return "Error generating speech", 400


@app.route("/cache/<text>/<providerId>/<voiceId>", methods=["POST", "GET"])
def cacheData(text: str, providerId: str = "", voiceId: str = ""):
    if not config.cacheData:
        return jsonify(False)
    text = unquote(text).lower()
    providerId = unquote(providerId)
    voiceId = unquote(voiceId)
    speechManager.getSpeakData(text, providerId, voiceId)
    return jsonify(True)


@app.route("/speaking/", methods=["GET"])
def speaking():
    speaking = speechManager.isSpeaking()
    return jsonify(speaking)


@app.route("/stop/", methods=["GET", "POST"])
def stop():
    speechManager.stop()
    return jsonify(True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, threaded=True)
