#!/usr/bin/env python

import io
import logging
import os
import sys
from urllib.parse import unquote

from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from flask_restx import Api, Resource, fields

# Add the parent directory to sys.path for imports when running as executable
if getattr(sys, "frozen", False):
    # we are running in a bundle
    bundle_dir = sys._MEIPASS
    # Set template folder for frozen app
    app = Flask(
        __name__, template_folder=os.path.join(bundle_dir, "speech", "templates")
    )
else:
    # we are running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

app.url_map.strict_slashes = False
CORS(app)

sys.path.append(os.path.dirname(bundle_dir))

try:
    from speech.audio_manager import AudioManager
    from speech.config_manager import ConfigManager
    from speech.provider_factory import TTSProviderFactory
except ImportError:
    # Fallback for when running as module
    from audio_manager import AudioManager
    from config_manager import ConfigManager
    from provider_factory import TTSProviderFactory

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# HTTP status codes
HTTP_NOT_FOUND = 404

# Create configuration manager instance
config_manager = ConfigManager()

# Create provider factory and audio manager
provider_factory = TTSProviderFactory()
audio_manager = AudioManager()

# Initialize providers with configuration
config = config_manager.get_tts_config()
providers = {}
for engine_type in config.get("engines", []):
    provider = provider_factory.create_provider(engine_type, config)
    if provider:
        providers[engine_type] = provider
        logger.info(f"Successfully initialized {engine_type} provider")
    else:
        logger.error(f"Failed to initialize {engine_type} provider")

# Initialize Flask-RESTX
api = Api(
    app,
    version="1.0",
    title="AsTeRICS Grid Speech API",
    description="API for text-to-speech functionality in AsTeRICS Grid. All endpoints are prefixed with /api.",
    doc="/docs",
    prefix="/api",
)

# Define namespaces
ns = api.namespace(
    "", description="Speech synthesis operations. All endpoints are prefixed with /api."
)

# Define models
root_response = api.model(
    "RootResponse",
    {
        "name": fields.String(
            description="API name", example="AsTeRICS Grid Speech API"
        ),
        "version": fields.String(description="API version", example="1.0"),
        "description": fields.String(
            description="API description",
            example="API for text-to-speech functionality in AsTeRICS Grid",
        ),
        "documentation": fields.String(
            description="Link to API documentation", example="/docs"
        ),
        "endpoints": fields.Raw(
            description="Available API endpoints (all prefixed with /api)",
            example={
                "voices": "/api/voices",
                "speak": "/api/speak/<text>/<provider_id>/<voice_id>",
                "speakdata": "/api/speakdata/<text>/<provider_id>/<voice_id>",
                "speaking": "/api/speaking",
                "stop": "/api/stop",
            },
        ),
    },
)


# Root route for web interface
@app.route("/")
def index():
    """Main configuration page for the speech service."""
    return render_template(
        "config.html",
        config=config_manager.config,
        available_engines=config_manager.get_available_engines(),
        enabled_engines=config_manager.get_enabled_engines(),
        validation_errors={},
        success_message=None,
        error_message=None,
    )


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
                                        f"Error reading JSON file: {e!s}"
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
                # Reinitialize providers with new configuration
                config = config_manager.get_tts_config()
                providers = {}
                for engine_type in config.get("engines", []):
                    provider = provider_factory.create_provider(engine_type, config)
                    if provider:
                        providers[engine_type] = provider
                        logger.info(f"Successfully initialized {engine_type} provider")
                    else:
                        logger.error(f"Failed to initialize {engine_type} provider")
                success_message = "Configuration saved successfully"
            else:
                error_message = "Please fix the configuration errors"

        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            error_message = f"Error saving configuration: {e!s}"

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
                "voices": "/api/voices",
                "speak": "/api/speak/<text>/<provider_id>/<voice_id>",
                "speakdata": "/api/speakdata/<text>/<provider_id>/<voice_id>",
                "speaking": "/api/speaking",
                "stop": "/api/stop",
            },
        }


# Define models
voice_model = api.model(
    "Voice",
    {
        "id": fields.String(
            description="Unique identifier for the voice", example="en-us-amy-medium"
        ),
        "name": fields.String(
            description="Display name of the voice", example="Amy (en-US) - sherpaonnx"
        ),
        "language": fields.String(description="Primary language code", example="en-US"),
        "language_codes": fields.List(
            fields.String, description="Supported language codes", example=["en-US"]
        ),
        "gender": fields.String(description="Voice gender (M/F/N)", example="F"),
        "providerId": fields.String(
            description="ID of the TTS provider", example="sherpaonnx"
        ),
        "type": fields.String(
            description="Type of voice playback", example="external_playing"
        ),
    },
)

voices_response = api.model(
    "VoicesResponse",
    {
        "voices": fields.List(
            fields.Nested(voice_model), description="List of available voices"
        ),
        "status": fields.String(
            description="Response status (success/error)", example="success"
        ),
        "error": fields.String(
            description="Error message if status is error", required=False
        ),
    },
)

error_response = api.model(
    "ErrorResponse",
    {
        "error": fields.String(
            description="Error message", example="Failed to generate speech data"
        ),
        "status": fields.String(description="Response status (error)", example="error"),
    },
)

success_response = api.model(
    "SuccessResponse",
    {
        "status": fields.String(
            description="Response status (success)", example="success"
        ),
    },
)

speaking_response = api.model(
    "SpeakingResponse",
    {
        "speaking": fields.Boolean(
            description="Whether text is currently being spoken", example=False
        ),
        "status": fields.String(
            description="Response status (success)", example="success"
        ),
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


langcodes_param = ns.model(
    "LangcodesParam",
    {
        "langcodes": fields.String(
            description="Language code format to return",
            enum=["bcp47", "iso639_3", "display", "all"],
            default="bcp47",
            required=False,
        )
    },
)


@ns.route("/voices")
class Voices(Resource):
    @ns.doc(
        "get_voices",
        description="Get a list of all available voices from all configured TTS providers",
        responses={200: "Successfully retrieved voices", 500: "Internal server error"},
    )
    @ns.response(200, "Success", voices_response)
    @ns.response(500, "Error", error_response)
    @ns.param(
        "langcodes",
        "Language code format to return (bcp47, iso639_3, display, or all)",
        _in="query",
        default="bcp47",
    )
    def get(self):
        """Get available voices from all providers."""
        try:
            # Get langcodes parameter from query string
            langcodes = request.args.get("langcodes", "bcp47")
            if langcodes not in ["bcp47", "iso639_3", "display", "all"]:
                langcodes = "bcp47"  # Default to BCP-47 format

            voices = []
            for provider_id, provider in providers.items():
                try:
                    provider_voices = provider.get_voices(langcodes=langcodes)
                    for voice in provider_voices:
                        voice["providerId"] = provider_id
                        voices.append(voice)
                except Exception as e:
                    logger.error(f"Error getting voices from {provider_id}: {e}")
                    continue

            if not voices:
                logger.warning("No voices available")
                return {"status": "error", "error": "No voices available", "voices": []}

            return {"status": "success", "voices": voices}
        except Exception as e:
            logger.error(f"Error in /voices endpoint: {e}", exc_info=True)
            return {"status": "error", "error": str(e), "voices": []}


@ns.route("/speakdata/<string:text>")
@ns.route("/speakdata/<string:text>/<string:provider_id>")
@ns.route("/speakdata/<string:text>/<string:provider_id>/<path:voice_id>")
class SpeakData(Resource):
    @ns.doc(
        "get_speak_data",
        description="Generate WAV audio data for the given text using specified voice",
        params={
            "text": "Text to convert to speech (URL encoded)",
            "provider_id": "ID of the TTS provider to use (optional)",
            "voice_id": "ID of the voice to use (optional)",
        },
        responses={
            200: "Successfully generated speech data",
            500: "Internal server error",
        },
    )
    @ns.param("text", "Text to convert to speech", required=True)
    @ns.param("provider_id", "TTS provider ID", required=False)
    @ns.param("voice_id", "Voice ID to use", required=False)
    @ns.response(200, "Success")
    @ns.response(500, "Error", error_response)
    def get(self, text: str, provider_id: str = "", voice_id: str = ""):
        """Get speech data for text."""
        try:
            # Decode parameters
            text = unquote(text).lower()
            provider_id = unquote(provider_id)
            voice_id = unquote(voice_id)

            logger.info(f"Generating speech data for text: {text}, voice: {voice_id}")

            # Get provider and generate audio data
            provider = providers.get(provider_id)
            if not provider:
                logger.error(f"Provider {provider_id} not found")
                return {
                    "error": f"Provider {provider_id} not found",
                    "status": "error",
                }, 200

            audio_data = provider.get_speak_data(text, voice_id)
            if audio_data is None:
                logger.error("Failed to generate speech data")
                return {
                    "error": "Failed to generate speech data",
                    "status": "error",
                }, 200

            logger.info("Successfully generated speech data")
            return send_file(
                io.BytesIO(audio_data),
                mimetype="audio/wav",
                as_attachment=False,
                download_name="speech.wav",
            )
        except Exception as e:
            logger.error(f"Error in /speakdata endpoint: {e}", exc_info=True)
            return {"error": str(e), "status": "error"}, 200

    def post(self, text: str, provider_id: str = "", voice_id: str = ""):
        """POST method for speakdata endpoint."""
        return self.get(text, provider_id, voice_id)


@ns.route("/speak/<string:text>")
@ns.route("/speak/<string:text>/<string:provider_id>")
@ns.route("/speak/<string:text>/<string:provider_id>/<path:voice_id>")
class Speak(Resource):
    @ns.doc(
        "speak_text",
        description="Speak the given text using specified voice",
        params={
            "text": "Text to speak (URL encoded)",
            "provider_id": "ID of the TTS provider to use (optional)",
            "voice_id": "ID of the voice to use (optional)",
        },
        responses={200: "Successfully started speaking", 500: "Internal server error"},
    )
    @ns.param("text", "Text to speak", required=True)
    @ns.param("provider_id", "TTS provider ID", required=False)
    @ns.param("voice_id", "Voice ID to use", required=False)
    @ns.response(200, "Success", success_response)
    @ns.response(500, "Error", error_response)
    def get(self, text: str, provider_id: str = "", voice_id: str = ""):
        """Speak text using specified voice."""
        try:
            # Decode parameters
            text = unquote(text).lower()
            provider_id = unquote(provider_id)
            voice_id = unquote(voice_id)

            logger.info(f"Starting speech for text: {text}, voice: {voice_id}")

            # Get provider and generate audio data
            provider = providers.get(provider_id)
            if not provider:
                logger.error(f"Provider {provider_id} not found")
                return {
                    "error": f"Provider {provider_id} not found",
                    "status": "error",
                }, 200

            audio_data = provider.get_speak_data(text, voice_id)
            if audio_data is None:
                logger.error("Failed to generate speech data")
                return {
                    "error": "Failed to generate speech data",
                    "status": "error",
                }, 200

            # Start speaking with callbacks
            def on_complete():
                logger.info("Speech playback completed")

            def on_error(error):
                logger.error(f"Speech playback error: {error}")
                logger.debug(f"Error callback called with error: {error}")

            logger.debug("Starting audio playback with callbacks")
            logger.debug(f"Audio data size: {len(audio_data)} bytes")
            success = audio_manager.play_audio(audio_data, on_complete, on_error)
            if not success:
                logger.error("Failed to start speech")
                return {"error": "Failed to start speech", "status": "error"}, 200

            logger.info("Successfully started speech")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error in /speak endpoint: {e}", exc_info=True)
            return {"error": str(e), "status": "error"}, 200

    def post(self, text: str, provider_id: str = "", voice_id: str = ""):
        """POST method for speak endpoint."""
        return self.get(text, provider_id, voice_id)


@app.route("/cache/<text>/<provider_id>/<voice_id>", methods=["POST", "GET"])
def cache_data(text: str, provider_id: str = "", voice_id: str = ""):
    """Cache speech data for the given text."""
    try:
        # Check if caching is enabled
        if not config_manager.config["General"].get("cache_enabled", False):
            logger.info("Caching is disabled in configuration")
            return jsonify(
                {"status": "error", "message": "Caching is disabled in configuration"}
            )

        # Get cache directory from config
        cache_dir = config_manager.config["General"].get("cache_dir", "temp")
        logger.info(f"Using cache directory: {cache_dir}")

        # Decode parameters
        text = unquote(text).lower()
        provider_id = unquote(provider_id)
        voice_id = unquote(voice_id)

        # Get provider and generate audio data
        provider = providers.get(provider_id)
        if not provider:
            logger.error(f"Provider {provider_id} not found")
            return jsonify(
                {"status": "error", "message": f"Provider {provider_id} not found"}
            )

        # Get speech data (this will cache it if caching is enabled)
        logger.info(
            f"Attempting to cache speech data for text: {text}, voice: {voice_id}"
        )
        audio_data = provider.get_speak_data(text, voice_id)

        if audio_data:
            logger.info("Successfully cached speech data")
            return jsonify(
                {
                    "status": "success",
                    "message": "Speech data cached successfully",
                    "cache_dir": cache_dir,
                }
            )
        else:
            logger.error("Failed to generate speech data for caching")
            return jsonify(
                {"status": "error", "message": "Failed to generate speech data"}
            )

    except Exception as e:
        logger.error(f"Error in cache endpoint: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)})


@ns.route("/speaking")
class Speaking(Resource):
    @ns.doc(
        "is_speaking",
        description="Check if text is currently being spoken",
        responses={
            200: "Successfully retrieved speaking status",
            500: "Internal server error",
        },
    )
    @ns.response(200, "Success", speaking_response)
    @ns.response(500, "Error", error_response)
    def get(self):
        """Check if text is being spoken."""
        try:
            speaking = audio_manager.is_playing
            logger.debug(f"Speaking status: {speaking}")
            return {"speaking": speaking, "status": "success"}
        except Exception as e:
            logger.error(f"Error in /speaking endpoint: {e}", exc_info=True)
            return {"error": str(e), "status": "error", "speaking": False}, 200


@ns.route("/stop")
class Stop(Resource):
    @ns.doc(
        "stop_speaking",
        description="Stop the current speech playback",
        responses={200: "Successfully stopped speaking", 500: "Internal server error"},
    )
    @ns.response(200, "Success", success_response)
    @ns.response(500, "Error", error_response)
    def get(self):
        """Stop speaking."""
        try:
            logger.info("Stopping speech playback")
            audio_manager.stop_speaking()
            logger.info("Successfully stopped speech playback")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error in /stop endpoint: {e}", exc_info=True)
            return {"error": str(e), "status": "error"}, 200

    def post(self):
        """POST method for stop endpoint."""
        return self.get()


@app.route("/test")
def test():
    """Test page for trying out TTS endpoints."""
    return render_template("test.html")


def start_server(port=5555):
    """Start the Flask server."""
    try:
        # Start Flask server
        app.run(
            host="127.0.0.1",
            port=port,
            debug=False,  # Disable debug mode
            use_reloader=False,  # Disable the reloader
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start the speech service")
    parser.add_argument(
        "--port", type=int, default=5555, help="Port to run the server on"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Start the server
    start_server(port=args.port)
