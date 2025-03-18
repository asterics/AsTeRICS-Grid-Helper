from typing import Optional, List, Dict, Any
from provider_platform_data import provider as platform_provider
from provider_test_data import provider as test_provider

# List of all available providers
providers = [
    platform_provider,  # Platform-specific provider (eSpeak/AVSynth/SAPI)
    test_provider,
]

# Try to load optional providers
try:
    from provider_elevenlabs_data import provider as elevenlabs_provider

    providers.append(elevenlabs_provider)
except ImportError:
    print("Note: ElevenLabs provider not available (credentials missing)")

try:
    from provider_espeak_data import provider as espeak_provider

    providers.append(espeak_provider)
except Exception as e:
    print("Note: eSpeak provider not available:", str(e))

# Default provider is the platform-specific one
defaultProvider = platform_provider


def getVoices() -> List[Dict[str, Any]]:
    """Get all available voices from all providers."""
    voices = []
    for provider in providers:
        try:
            providerVoices = provider.getVoices()
            for voice in providerVoices:
                voice["providerId"] = provider.getProviderId()
                voice["type"] = provider.getVoiceType()
                voices.append(voice)
        except Exception as e:
            provider_id = provider.getProviderId()
            print(f"Error getting voices from provider {provider_id}: {str(e)}")
    return voices


def getSpeakData(
    text: str, voiceId: str, providerId: Optional[str] = None
) -> Optional[bytes]:
    """Get speech data for the given text and voice ID."""
    if providerId is None:
        providerId = defaultProvider.getProviderId()

    for provider in providers:
        if provider.getProviderId() == providerId:
            return provider.getSpeakData(text, voiceId)
    return None


def speak(text: str, providerId: str, voiceId: Optional[str] = None) -> None:
    """Speak the given text using the specified provider and voice."""
    if providerId not in [p.getProviderId() for p in providers]:
        print(f"ERROR: Unknown speech provider '{providerId}'!")
        return

    for provider in providers:
        if provider.getProviderId() == providerId:
            if voiceId:
                provider.tts.set_voice(voiceId)
            provider.tts.speak(text)
            return


def initProviders() -> None:
    """Initialize all speech providers."""
    for provider in providers:
        provider_id = provider.getProviderId()
        if not all(
            hasattr(provider, fn)
            for fn in ["getProviderId", "getVoiceType", "getVoices"]
        ):
            print(
                f"ERROR: speech provider '{provider_id}' is missing required functions!"
            )
            continue
