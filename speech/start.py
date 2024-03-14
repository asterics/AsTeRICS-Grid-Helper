#!/usr/bin/env python

from flask import Flask, jsonify, request
from flask_cors import CORS
import speechManager

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

@app.route('/voices/', methods=['GET'])
def voices():
    voices = speechManager.getVoices("azure")
    return jsonify(voices)


@app.route('/speak/<text>/', methods=['POST', 'GET'])
@app.route('/speak/<text>/<voiceId>', methods=['POST', 'GET'])
def speak(text, voiceId=None):
    speechManager.speak(text, "azure", voiceId)
    return jsonify(True)


@app.route('/speaking/', methods=['GET'])
def speaking():
    return jsonify(speechManager.isSpeaking())


@app.route('/stop/', methods=['GET', 'POST'])
def stop():
    speechManager.stop()
    return jsonify(True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=105, threaded=True)
