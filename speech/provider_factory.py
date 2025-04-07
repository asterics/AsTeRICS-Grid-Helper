"""Factory for creating TTS providers."""

import logging
from collections.abc import Callable
from typing import Any

# Import TTS wrapper clients
from tts_wrapper import (
    ElevenLabsClient,
    GoogleClient,
    GoogleTransClient,
    MicrosoftClient,
    PlayHTClient,
    PollyClient,
    SherpaOnnxClient,
    WatsonClient,
    WitAiClient,
    eSpeakClient,
)

from .audio_manager import AudioManager
from .custom_providers import OpenAITTSProvider
from .tts_provider import TTSProviderAbstract

logger = logging.getLogger(__name__)


class TTSProviderFactory:
    """Factory for creating TTS provider instances."""

    @staticmethod
    def create_wrapper_provider(tts_instance: Any) -> TTSProviderAbstract:
        """Create a provider that wraps a TTS wrapper instance."""

        class WrappedProvider(TTSProviderAbstract):
            """Wrapper for TTS providers that use the TTS library."""

            def __init__(self, tts_instance: Any):
                """Initialize the provider."""
                super().__init__()
                self.tts = tts_instance
                self._is_playing = False
                self._current_playback = None
                self._was_stopped = False
                self._on_start = None
                self._on_stop = None
                self._on_complete = None
                self.logger = logging.getLogger(__name__)
                self.logger.debug(
                    f"Initialized WrappedProvider with TTS instance: {tts_instance}"
                )

            def get_voices(self, langcodes: str = "bcp47") -> list[dict[str, Any]]:
                """Get available voices with specified language code format.

                Args:
                    langcodes: Language code format to return. Options are:
                        - "bcp47": BCP-47 format (default)
                        - "iso639_3": ISO 639-3 format
                        - "display": Human-readable display names
                        - "all": All formats in a dictionary

                Returns:
                    List of voice dictionaries
                """
                self.logger.debug(
                    f"Getting voices from TTS instance with langcodes={langcodes}"
                )
                voices = self.tts.get_voices(langcodes=langcodes) if self.tts else []
                self.logger.debug(f"Retrieved {len(voices)} voices")
                return voices

            def _generate_speak_data(self, text: str, voice_id: str) -> bytes | None:
                """Generate WAV audio data for text using specified voice."""
                try:
                    self.logger.debug(
                        f"Generating speech data for text: '{text}' with voice: {voice_id}"
                    )

                    if not self.tts:
                        self.logger.error("TTS instance not initialized")
                        return None

                    # In v1.0.0, we can use synth_to_bytes directly
                    if voice_id:
                        self.tts.set_voice(voice_id)

                    # Generate speech to bytes
                    audio_data = self.tts.synth_to_bytes(text)

                    if audio_data is None:
                        self.logger.error("Failed to generate audio data")
                        return None

                    self.logger.debug(f"Generated audio data: {len(audio_data)} bytes")
                    return audio_data

                except Exception as e:
                    self.logger.error(
                        f"Error generating speech data: {e}", exc_info=True
                    )
                    return None

            def speak_streamed(
                self,
                text: str,
                voice_id: str,
                on_start: Callable | None = None,
                on_end: Callable | None = None,
                on_word: Callable[[str, float, float], None] | None = None,
                on_error: Callable[[Exception], None] | None = None,
            ) -> bool:
                """Start streaming playback with callbacks."""
                self.logger.debug(
                    f"Starting streaming playback for text: '{text}' with voice: {voice_id}"
                )
                try:
                    if not self.tts:
                        self.logger.error("TTS instance not initialized")
                        raise RuntimeError("TTS instance not initialized")

                    # Connect callbacks if provided
                    if on_start:
                        self.logger.debug("Connecting on_start callback")
                        self.tts.connect("onStart", on_start)
                    if on_end:
                        self.logger.debug("Connecting on_end callback")
                        self.tts.connect("onEnd", on_end)
                    if on_word:
                        self.logger.debug("Connecting on_word callback")
                        self.tts.connect("onWord", on_word)

                    # Start streaming playback
                    self._is_playing = True
                    self.logger.debug("Setting _is_playing to True")

                    # In v1.0.0, all engines use the same interface
                    self._current_playback = self.tts.speak_streamed(
                        text, voice_id=voice_id
                    )

                    self.logger.debug("Streaming playback started successfully")
                    return True

                except Exception as e:
                    self.logger.error(
                        f"Error starting streaming playback: {e}", exc_info=True
                    )
                    if on_error:
                        self.logger.debug("Calling on_error callback")
                        on_error(e)
                    return False

            def stop_playback(self) -> bool:
                """Stop current streaming playback."""
                self.logger.debug("Attempting to stop playback")
                try:
                    if self._current_playback:
                        self.logger.debug("Stopping current playback")
                        self._current_playback.stop()
                        self._is_playing = False
                        self._current_playback = None
                        self.logger.debug("Playback stopped successfully")
                        return True
                    self.logger.debug("No current playback to stop")
                    return False
                except Exception as e:
                    self.logger.error(f"Error stopping playback: {e}", exc_info=True)
                    return False

            def speak(
                self, text: str, voice_id: str, on_complete: Callable | None = None
            ) -> bool:
                """Speak text using specified voice.

                Args:
                    text: Text to speak
                    voice_id: Voice ID to use
                    on_complete: Optional callback when playback completes

                Returns:
                    True if audio started playing, False if error occurred
                """
                try:
                    self.logger.debug(
                        f"Starting speech for text: '{text}' with voice: {voice_id}"
                    )

                    # Set up callbacks
                    def on_start_callback():
                        self.logger.debug("Speech started")
                        if self._on_start:
                            self._on_start()

                    def on_end_callback():
                        self.logger.debug("Speech ended")
                        if self._on_stop:
                            self._on_stop()
                        if not self._was_stopped and self._on_complete:
                            self._on_complete()
                        if not self._was_stopped and on_complete:
                            on_complete()
                        self._was_stopped = False
                        self._is_playing = False
                        self.logger.debug("Reset playback state after completion")

                    def on_error_callback(error):
                        self.logger.error(f"Speech error: {error}")
                        if self._on_stop:
                            self._on_stop()
                        if on_complete:
                            on_complete()
                        self._is_playing = False
                        self.logger.debug("Reset playback state after error")

                    # Reset stop flag and ensure we're not playing
                    self._was_stopped = False
                    self._is_playing = False
                    self.logger.debug("Reset playback state before starting")

                    # Get audio data using parent class method
                    audio_data = self.get_speak_data(text, voice_id)
                    if not audio_data:
                        self.logger.error("Failed to generate audio data")
                        return False

                    # Start playback with callbacks
                    success = self.audio_manager.play_audio(
                        audio_data,
                        on_complete=on_end_callback,
                        on_error=on_error_callback,
                    )

                    if success:
                        on_start_callback()
                    else:
                        on_error_callback(RuntimeError("Failed to start playback"))

                    return success

                except Exception as e:
                    self.logger.error(f"Error in speak: {e}", exc_info=True)
                    if on_complete:
                        on_complete()
                    self._is_playing = False
                    self.logger.debug("Reset playback state after exception")
                    return False

            def stop_speaking(self) -> None:
                """Stop current speech playback."""
                if self.is_speaking:
                    self.logger.debug("Stopping speech playback")
                    self._was_stopped = True
                    self.stop_playback()
                    if self._on_stop:
                        self._on_stop()
                    self._is_playing = False
                    self.logger.debug("Reset playback state after stop")

            @property
            def is_speaking(self) -> bool:
                """Check if audio is currently playing."""
                return self._is_playing

        return WrappedProvider(tts_instance)

    @staticmethod
    def create_provider(
        engine_type: str, config: dict[str, Any]
    ) -> TTSProviderAbstract | None:
        """Create a TTS provider instance based on engine type."""
        try:
            logger.debug(f"Creating provider for engine type: {engine_type}")
            logger.debug(f"Config: {config}")

            # Get engine configuration
            engine_configs = config.get("engine_configs", {})
            logger.debug(f"Engine configs: {engine_configs}")

            engine_config = engine_configs.get(engine_type, {})
            logger.debug(f"Engine config for {engine_type}: {engine_config}")

            # Only check for empty config for engines that need credentials
            if engine_type not in ["sherpaonnx", "espeak"] and not engine_config:
                logger.error(f"No configuration found for engine type: {engine_type}")
                return None

            # Create TTS instance based on engine type
            tts_instance = None
            if engine_type == "microsoft":
                credentials = engine_config.get("credentials", ("", ""))
                if not credentials[0] or not credentials[1]:
                    logger.error("Missing Microsoft credentials")
                    return None
                # Create client first, then set voice separately
                voice_id = engine_config.get("voice_id", None)
                tts_instance = MicrosoftClient(credentials=credentials)
                if voice_id:
                    tts_instance.set_voice(voice_id)
            elif engine_type == "google":
                credentials = engine_config.get("credentials", {})
                voice_id = engine_config.get("voice_id", None)
                tts_instance = GoogleClient(credentials=credentials)
                if voice_id:
                    tts_instance.set_voice(voice_id)
            elif engine_type == "googletrans":
                voice_id = engine_config.get("voice_id", "en-us")
                tts_instance = GoogleTransClient()
                if voice_id:
                    tts_instance.set_voice(voice_id)
            elif engine_type == "elevenlabs":
                credentials = engine_config.get("credentials", ("",))
                voice_id = engine_config.get("voice_id", None)
                tts_instance = ElevenLabsClient(credentials=credentials)
                if voice_id:
                    tts_instance.set_voice(voice_id)
            elif engine_type == "polly":
                credentials = engine_config.get("credentials", ("", "", ""))
                voice_id = engine_config.get("voice_id", None)
                tts_instance = PollyClient(credentials=credentials)
                if voice_id:
                    tts_instance.set_voice(voice_id)
            elif engine_type == "watson":
                credentials = engine_config.get("credentials", ("", "", ""))
                voice_id = engine_config.get("voice_id", None)
                tts_instance = WatsonClient(credentials=credentials)
                if voice_id:
                    tts_instance.set_voice(voice_id)
            elif engine_type == "witai":
                credentials = engine_config.get("credentials", ("",))
                voice_id = engine_config.get("voice_id", None)
                tts_instance = WitAiClient(credentials=credentials)
                if voice_id:
                    tts_instance.set_voice(voice_id)
            elif engine_type == "playht":
                credentials = engine_config.get("credentials", ("", ""))
                voice_id = engine_config.get("voice_id", None)
                tts_instance = PlayHTClient(credentials=credentials)
                if voice_id:
                    tts_instance.set_voice(voice_id)
            elif engine_type == "sherpaonnx":
                # Get voice and language from config if available
                voice = engine_config.get("voice", None)
                lang = engine_config.get("lang", None)
                tts_instance = SherpaOnnxClient()
                # Set voice and language if provided
                if voice:
                    tts_instance.set_voice(voice)
                if lang:
                    tts_instance.set_lang(lang)
                logger.debug(
                    f"Created SherpaOnnxClient with lang={lang}, voice={voice}"
                )
            elif engine_type == "espeak":
                voice_id = engine_config.get("voice_id", None)
                tts_instance = eSpeakClient()
                if voice_id:
                    tts_instance.set_voice(voice_id)
            elif engine_type == "openai":
                # Create OpenAI provider directly
                openai_provider = OpenAITTSProvider(engine_config)
                # Set audio manager for the provider
                openai_provider.audio_manager = AudioManager()
                return openai_provider
            else:
                logger.error(f"Unsupported engine type: {engine_type}")
                return None

            if not tts_instance:
                logger.error(f"Failed to create TTS instance for {engine_type}")
                return None

            # Create wrapped provider
            return TTSProviderFactory.create_wrapper_provider(tts_instance)

        except Exception as e:
            logger.error(f"Error creating provider {engine_type}: {e}", exc_info=True)
            return None
