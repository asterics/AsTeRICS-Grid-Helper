#!/usr/bin/env python

import io
import logging
import os
import sys
from urllib.parse import unquote

from flask import Flask, jsonify, send_file
from flask_cors import CORS
from flask_restx import Api, Resource, fields

from .config import CACHE_ENABLED
from .speech_manager import (
    get_speak_data,
    get_voices,
    init_providers,
    is_speaking,
    speak,
    stop_speaking,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

# Initialize Flask-RESTX
api = Api(
    app,
    version="1.0",
    title="AsTeRICS Grid Speech API",
    description="API for text-to-speech functionality in AsTeRICS Grid",
    doc="/docs",
)

# Define namespaces
ns = api.namespace("", description="Speech synthesis operations")

# Define models
voice_model = api.model(
    "Voice",
    {
        "id": fields.String(description="Unique identifier for the voice"),
        "name": fields.String(description="Display name of the voice"),
        "language_codes": fields.List(
            fields.String, description="Supported language codes"
        ),
        "gender": fields.String(description="Voice gender (M/F/N)"),
    },
)

voices_response = api.model(
    "VoicesResponse",
    {
        "voices": fields.List(
            fields.Nested(voice_model), description="List of available voices"
        ),
        "status": fields.String(description="Response status (success/error)"),
        "error": fields.String(
            description="Error message if status is error", required=False
        ),
    },
)

error_response = api.model(
    "ErrorResponse",
    {
        "error": fields.String(description="Error message"),
        "status": fields.String(description="Response status (error)"),
    },
)

success_response = api.model(
    "SuccessResponse",
    {
        "status": fields.String(description="Response status (success)"),
    },
)

speaking_response = api.model(
    "SpeakingResponse",
    {
        "speaking": fields.Boolean(
            description="Whether text is currently being spoken"
        ),
        "status": fields.String(description="Response status (success)"),
    },
)

# Initialize speech provider
init_providers()


# Error handler for all exceptions
@app.errorhandler(Exception)
def handle_error(error):
    """Handle all exceptions and return them as JSON responses."""
    logger.error(f"Error: {error!s}", exc_info=True)
    return jsonify({"error": str(error), "status": "error"}), 200


@ns.route("/voices")
class Voices(Resource):
    @ns.doc("get_voices")
    @ns.response(200, "Success", voices_response)
    @ns.response(500, "Error", error_response)
    def get(self):
        """Get available voices."""
        try:
            voices = get_voices()
            return {"voices": voices, "status": "success"}
        except Exception as e:
            logger.error(f"Error in /voices endpoint: {e!s}", exc_info=True)
            return {"error": str(e), "status": "error", "voices": []}, 200


@ns.route("/speakdata/<string:text>/<string:provider_id>/<string:voice_id>")
class SpeakData(Resource):
    @ns.doc("get_speak_data")
    @ns.param("text", "Text to convert to speech")
    @ns.param("provider_id", "TTS provider ID")
    @ns.param("voice_id", "Voice ID to use")
    @ns.response(200, "Success")
    @ns.response(500, "Error", error_response)
    def get(self, text: str, provider_id: str, voice_id: str):
        """Get speech data for text."""
        try:
            data = get_speak_data(text, voice_id, provider_id)
            if data is None:
                return {
                    "error": "Failed to generate speech data",
                    "status": "error",
                }, 200
            return send_file(
                io.BytesIO(data),
                mimetype="audio/wav",
                as_attachment=True,
                download_name="speech.wav",
            )
        except Exception as e:
            logger.error(f"Error in /speakdata endpoint: {e!s}", exc_info=True)
            return {"error": str(e), "status": "error"}, 200


@ns.route("/speak/<string:text>/<string:provider_id>/<string:voice_id>")
class Speak(Resource):
    @ns.doc("speak_text")
    @ns.param("text", "Text to speak")
    @ns.param("provider_id", "TTS provider ID")
    @ns.param("voice_id", "Voice ID to use")
    @ns.response(200, "Success", success_response)
    @ns.response(500, "Error", error_response)
    def get(self, text: str, provider_id: str, voice_id: str):
        """Speak text using specified voice."""
        try:
            speak(text, provider_id, voice_id)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error in /speak endpoint: {e!s}", exc_info=True)
            return {"error": str(e), "status": "error"}, 200


@app.route("/cache/<text>/<provider_id>/<voice_id>", methods=["POST", "GET"])
def cache_data(text: str, provider_id: str = "", voice_id: str = ""):
    """Cache speech data for the given text."""
    if not CACHE_ENABLED:
        return jsonify(False)
    text = unquote(text).lower()
    provider_id = unquote(provider_id)
    voice_id = unquote(voice_id)
    get_speak_data(text, voice_id, provider_id)
    return jsonify(True)


@ns.route("/speaking")
class Speaking(Resource):
    @ns.doc("is_speaking")
    @ns.response(200, "Success", speaking_response)
    @ns.response(500, "Error", error_response)
    def get(self):
        """Check if text is being spoken."""
        try:
            speaking = is_speaking()
            return {"speaking": speaking, "status": "success"}
        except Exception as e:
            logger.error(f"Error in /speaking endpoint: {e!s}", exc_info=True)
            return {"error": str(e), "status": "error", "speaking": False}, 200


@ns.route("/stop")
class Stop(Resource):
    @ns.doc("stop_speaking")
    @ns.response(200, "Success", success_response)
    @ns.response(500, "Error", error_response)
    def get(self):
        """Stop speaking."""
        try:
            stop_speaking()
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error in /stop endpoint: {e!s}", exc_info=True)
            return {"error": str(e), "status": "error"}, 200


def start_server(host: str = "127.0.0.1", port: int = 5555) -> None:
    """Start the Flask server."""
    init_providers()
    app.run(host=host, port=port)


if __name__ == "__main__":
    start_server()
