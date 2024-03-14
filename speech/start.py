#!/usr/bin/env python

from flask import Flask, jsonify, request
from flask_cors import CORS
import speechManager

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

@app.route('/voices/', methods=['GET'])
def voices():
    voices = speechManager.getVoices()
    return jsonify(voices)


@app.route('/speak/<text>/', methods=['POST', 'GET'])
@app.route('/speak/<text>/<providerId>/', methods=['POST', 'GET'])
@app.route('/speak/<text>/<providerId>/<voiceId>', methods=['POST', 'GET'])
def speak(text, providerId=None, voiceId=None):
    speechManager.speak(text, providerId, voiceId)
    return jsonify(True)


@app.route('/speaking/', methods=['GET'])
def speaking():
    speaking = speechManager.isSpeaking()
    return jsonify(speaking)


@app.route('/stop/', methods=['GET', 'POST'])
def stop():
    speechManager.stop()
    return jsonify(True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=105, threaded=True)
