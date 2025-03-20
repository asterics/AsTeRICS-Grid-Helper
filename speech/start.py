#!/usr/bin/env python

import io
import logging
from urllib.parse import unquote

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_restx import Api, Resource, fields

from .config import CACHE_ENABLED
from .speech_manager import (
    SpeechManager,
    get_speak_data,
    get_voices,
    is_speaking,
    speak,
    stop_speaking,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# HTTP status codes
HTTP_NOT_FOUND = 404

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

# Create speech manager instance
speech_manager = SpeechManager()

# Initialize Flask-RESTX
api = Api(
    app,
    version="1.0",
    title="AsTeRICS Grid Speech API",
    description="API for text-to-speech functionality in AsTeRICS Grid",
    doc="/docs",
    prefix="/api",  # Add a prefix to avoid conflicts with Flask routes
)

# Define namespaces
ns = api.namespace("", description="Speech synthesis operations")

# Define models
root_response = api.model(
    "RootResponse",
    {
        "name": fields.String(description="API name"),
        "version": fields.String(description="API version"),
        "description": fields.String(description="API description"),
        "documentation": fields.String(description="Link to API documentation"),
        "endpoints": fields.Raw(description="Available API endpoints"),
    },
)


@ns.route("/")
class Root(Resource):
    @ns.doc("get_root")
    @ns.response(200, "Success", root_response)
    def get(self):
        """Return basic API information and documentation link."""
        return {
            "name": "AsTeRICS Grid Speech API",
            "version": "1.0",
            "description": "API for text-to-speech functionality in AsTeRICS Grid",
            "documentation": "/docs",
            "endpoints": {
                "voices": "/voices",
                "speak": "/speak/<text>/<provider_id>/<voice_id>",
                "speakdata": "/speakdata/<text>/<provider_id>/<voice_id>",
                "speaking": "/speaking",
                "stop": "/stop",
            },
        }


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


# Error handler for all exceptions
@app.errorhandler(Exception)
def handle_error(error):
    """Handle all exceptions and return them as JSON responses."""
    # Let Flask-RESTX handle its own routes
    if (
        hasattr(error, "code")
        and error.code == HTTP_NOT_FOUND
        and request.path.startswith("/")
    ):
        return error
    logger.error(f"Error: {error!s}", exc_info=True)
    return jsonify({"error": str(error), "status": "error"}), 200


@ns.route("/voices")
class Voices(Resource):
    @ns.doc("get_voices")
    @ns.response(200, "Success", voices_response)
    @ns.response(500, "Error", error_response)
    def get(self):
        """Get available voices from all providers."""
        try:
            voices = get_voices(speech_manager)
            return {"voices": voices, "status": "success"}
        except Exception as e:
            logger.error(f"Error in /voices endpoint: {e!s}", exc_info=True)
            return {"error": str(e), "status": "error", "voices": []}, 200


@ns.route("/speakdata/<string:text>")
@ns.route("/speakdata/<string:text>/<string:provider_id>")
@ns.route("/speakdata/<string:text>/<string:provider_id>/<string:voice_id>")
class SpeakData(Resource):
    @ns.doc("get_speak_data")
    @ns.param("text", "Text to convert to speech")
    @ns.param("provider_id", "TTS provider ID", required=False)
    @ns.param("voice_id", "Voice ID to use", required=False)
    @ns.response(200, "Success")
    @ns.response(500, "Error", error_response)
    def get(self, text: str, provider_id: str = "", voice_id: str = ""):
        """Get speech data for text."""
        try:
            text = unquote(text).lower()
            provider_id = unquote(provider_id)
            voice_id = unquote(voice_id)
            data = get_speak_data(text, voice_id, provider_id, speech_manager)
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

    def post(self, text: str, provider_id: str = "", voice_id: str = ""):
        """POST method for speakdata endpoint."""
        return self.get(text, provider_id, voice_id)


@ns.route("/speak/<string:text>")
@ns.route("/speak/<string:text>/<string:provider_id>")
@ns.route("/speak/<string:text>/<string:provider_id>/<string:voice_id>")
class Speak(Resource):
    @ns.doc("speak_text")
    @ns.param("text", "Text to speak")
    @ns.param("provider_id", "TTS provider ID", required=False)
    @ns.param("voice_id", "Voice ID to use", required=False)
    @ns.response(200, "Success", success_response)
    @ns.response(500, "Error", error_response)
    def get(self, text: str, provider_id: str = "", voice_id: str = ""):
        """Speak text using specified voice."""
        try:
            text = unquote(text).lower()
            provider_id = unquote(provider_id)
            voice_id = unquote(voice_id)
            speak(text, provider_id, voice_id, speech_manager)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error in /speak endpoint: {e!s}", exc_info=True)
            return {"error": str(e), "status": "error"}, 200

    def post(self, text: str, provider_id: str = "", voice_id: str = ""):
        """POST method for speak endpoint."""
        return self.get(text, provider_id, voice_id)


@app.route("/cache/<text>/<provider_id>/<voice_id>", methods=["POST", "GET"])
def cache_data(text: str, provider_id: str = "", voice_id: str = ""):
    """Cache speech data for the given text."""
    if not CACHE_ENABLED:
        return jsonify(False)
    text = unquote(text).lower()
    provider_id = unquote(provider_id)
    voice_id = unquote(voice_id)
    get_speak_data(text, voice_id, provider_id, speech_manager)
    return jsonify(True)


@ns.route("/speaking")
class Speaking(Resource):
    @ns.doc("is_speaking")
    @ns.response(200, "Success", speaking_response)
    @ns.response(500, "Error", error_response)
    def get(self):
        """Check if text is being spoken."""
        try:
            speaking = is_speaking(speech_manager)
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
            stop_speaking(speech_manager)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error in /stop endpoint: {e!s}", exc_info=True)
            return {"error": str(e), "status": "error"}, 200

    def post(self):
        """POST method for stop endpoint."""
        return self.get()


def start_server():
    """Start the Flask server."""
    try:
        # Initialize speech providers
        speech_manager.init_providers()

        # Start Flask server
        app.run(
            host="127.0.0.1",
            port=5555,
            debug=True,  # Keep debug mode for error reporting
            use_reloader=False,  # Disable the reloader to prevent double initialization
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    start_server()
