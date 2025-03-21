#!/usr/bin/env python

import io
import logging
import os
import sys
from urllib.parse import unquote
from flask import Flask, jsonify, request, send_file, render_template, redirect, url_for
from flask_cors import CORS
from flask_restx import Api, Resource, fields

# Add the parent directory to sys.path for imports when running as executable
if getattr(sys, "frozen", False):
    # we are running in a bundle
    bundle_dir = sys._MEIPASS
else:
    # we are running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.dirname(bundle_dir))

try:
    from speech.config_manager import ConfigManager
    from speech.speech_manager import (
        SpeechManager,
        get_speak_data,
        get_voices,
        is_speaking,
        speak,
        stop_speaking,
    )
except ImportError:
    # Fallback for when running as module
    from config_manager import ConfigManager
    from speech_manager import (
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

# Create configuration manager instance
config_manager = ConfigManager()

# Create speech manager instance
speech_manager = SpeechManager()

# Initialize Flask-RESTX
api = Api(
    app,
    version="1.0",
    title="AsTeRICS Grid Speech API",
    description="API for text-to-speech functionality in AsTeRICS Grid",
    doc="/docs",
    prefix="/api",
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


@app.route("/")
def index():
    """Main configuration page for the speech service."""
    return config()


@app.route("/config", methods=["GET", "POST"])
def config():
    """Configuration page for the speech service."""
    validation_errors = {}
    success_message = None
    error_message = None

    if request.method == "POST":
        try:
            # Update general settings
            config_manager.config["General"]["cache_enabled"] = str(
                bool(request.form.get("cache_enabled"))
            )
            config_manager.config["General"]["cache_dir"] = request.form.get(
                "cache_dir", "temp"
            )

            # Get enabled engines
            enabled_engines = request.form.getlist("enabled_engines")
            config_manager.set_enabled_engines(enabled_engines)

            # Update engine configurations
            for engine in config_manager.get_available_engines():
                if engine.name in enabled_engines:
                    engine_config = {}

                    # Special handling for Google Cloud credentials
                    if engine.name == "google":
                        # Check for file upload first
                        if "google_credentials_file" in request.files:
                            file = request.files["google_credentials_file"]
                            if file and file.filename.endswith(".json"):
                                try:
                                    credentials_json = file.read().decode("utf-8")
                                    engine_config["credentials_json"] = credentials_json
                                except Exception as e:
                                    validation_errors["google"] = [
                                        f"Error reading JSON file: {str(e)}"
                                    ]
                        # If no file uploaded, check for pasted JSON
                        if not engine_config and request.form.get(
                            "google_credentials_json"
                        ):
                            engine_config["credentials_json"] = request.form.get(
                                "google_credentials_json"
                            )
                    else:
                        # Standard field handling for other engines
                        for field in engine.required_fields:
                            field_name = f"{engine.name}_{field}"
                            engine_config[field] = request.form.get(field_name, "")

                    config_manager.set_engine_config(engine.name, engine_config)

            # Validate configurations
            all_valid = True
            for engine in enabled_engines:
                errors = config_manager.validate_engine_config(engine)
                if errors:
                    validation_errors[engine] = errors
                    all_valid = False

            if all_valid:
                config_manager.save_config()
                # Reinitialize speech manager with new configuration
                speech_manager.init_providers(config_manager.get_tts_config())
                success_message = "Configuration saved successfully"
            else:
                error_message = "Please fix the configuration errors"

        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            error_message = f"Error saving configuration: {str(e)}"

    return render_template(
        "config.html",
        config=config_manager.config,
        available_engines=config_manager.get_available_engines(),
        enabled_engines=config_manager.get_enabled_engines(),
        validation_errors=validation_errors,
        success_message=success_message,
        error_message=error_message,
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


def create_wav_header(pcm_data: bytes) -> bytes:
    """Create a WAV header for the PCM data."""
    # WAV header parameters
    sample_rate = 16000  # Standard sample rate for speech
    bits_per_sample = 16  # 16-bit audio
    channels = 1  # Mono audio
    data_size = len(pcm_data)

    # WAV header (44 bytes)
    header = bytearray()
    header.extend(b"RIFF")  # ChunkID
    header.extend((36 + data_size).to_bytes(4, "little"))  # ChunkSize
    header.extend(b"WAVE")  # Format
    header.extend(b"fmt ")  # Subchunk1ID
    header.extend((16).to_bytes(4, "little"))  # Subchunk1Size
    header.extend((1).to_bytes(2, "little"))  # AudioFormat (1 = PCM)
    header.extend(channels.to_bytes(2, "little"))  # NumChannels
    header.extend(sample_rate.to_bytes(4, "little"))  # SampleRate
    header.extend(
        (sample_rate * channels * bits_per_sample // 8).to_bytes(4, "little")
    )  # ByteRate
    header.extend((channels * bits_per_sample // 8).to_bytes(2, "little"))  # BlockAlign
    header.extend(bits_per_sample.to_bytes(2, "little"))  # BitsPerSample
    header.extend(b"data")  # Subchunk2ID
    header.extend(data_size.to_bytes(4, "little"))  # Subchunk2Size

    return bytes(header)


@ns.route("/speakdata/<string:text>")
@ns.route("/speakdata/<string:text>/<string:provider_id>")
@ns.route("/speakdata/<string:text>/<string:provider_id>/<path:voice_id>")
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

            # Add WAV header to the PCM data
            wav_data = create_wav_header(data) + data
            return send_file(
                io.BytesIO(wav_data),
                mimetype="audio/wav",
                as_attachment=False,
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
@ns.route("/speak/<string:text>/<string:provider_id>/<path:voice_id>")
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
            speak(text, voice_id, provider_id, speech_manager)
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
    if not config_manager.config["General"]["cache_enabled"]:
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


@app.route("/test")
def test():
    """Test page for trying out TTS endpoints."""
    return render_template("test.html")


def start_server():
    """Start the Flask server."""
    try:
        # Initialize speech providers with configuration
        speech_manager.init_providers(config_manager.get_tts_config())

        # Start Flask server
        app.run(
            host="127.0.0.1",
            port=5555,
            debug=False,  # Disable debug mode
            use_reloader=False,  # Disable the reloader
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    start_server()
