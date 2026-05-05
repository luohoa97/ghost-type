"""STT fallback chain for GhostType."""
from typing import List, Optional, Dict, Any
from ghosttype.core.errors import STTError, ProviderUnavailable, ProviderNotConfigured
from ghosttype.providers.stt.base import STTProvider


class STTFallbackChain:
    """Manages a chain of STT providers with fallback support."""
    
    def __init__(self, providers: List[STTProvider]):
        self.providers = providers
        self._current_provider_index = 0
    
    @property
    def current_provider(self) -> Optional[STTProvider]:
        """Get the current provider in the chain."""
        if self._current_provider_index < len(self.providers):
            return self.providers[self._current_provider_index]
        return None
    
    def transcribe(self, audio_bytes: bytes, options: Optional[Dict[str, Any]] = None) -> str:
        """Transcribe audio using the fallback chain."""
        if options is None:
            options = {}
        
        # Try each provider in order
        for i, provider in enumerate(self.providers):
            try:
                # Check if provider is available
                if not provider.is_available():
                    raise ProviderUnavailable(f"Provider {provider.id} is not available")
                
                # Try transcription
                result = provider.transcribe(audio_bytes, options)
                self._current_provider_index = i
                return result
                
            except (ProviderUnavailable, ProviderNotConfigured, STTError) as e:
                # Try next provider
                if i < len(self.providers) - 1:
                    continue
                else:
                    # Last provider failed
                    raise STTError(
                        f"All STT providers failed: {str(e)}. "
                        "Check your configuration and dependencies."
                    )
        
        raise STTError("No STT providers available")
    
    def stream_transcribe(
        self,
        audio_stream,
        options: Optional[Dict[str, Any]] = None
    ):
        """Stream transcribe audio using the fallback chain."""
        if options is None:
            options = {}
        
        # Try each provider in order
        for i, provider in enumerate(self.providers):
            try:
                # Check if provider is available
                if not provider.is_available():
                    raise ProviderUnavailable(f"Provider {provider.id} is not available")
                
                # Check if provider supports streaming
                if not provider.supports_streaming():
                    continue
                
                # Try streaming transcription
                result = provider.stream_transcribe(audio_stream, options)
                self._current_provider_index = i
                return result
                
            except (ProviderUnavailable, ProviderNotConfigured, STTError) as e:
                # Try next provider
                if i < len(self.providers) - 1:
                    continue
                else:
                    # Last provider failed
                    raise STTError(
                        f"All STT providers failed: {str(e)}. "
                        "Check your configuration and dependencies."
                    )
        
        raise STTError("No STT providers with streaming support available")
    
    def is_available(self) -> bool:
        """Check if any provider in the chain is available."""
        return any(p.is_available() for p in self.providers)
    
    def get_available_providers(self) -> List[STTProvider]:
        """Get list of available providers in the chain."""
        return [p for p in self.providers if p.is_available()]
    
    def diagnostics(self) -> Dict[str, Any]:
        """Get diagnostics for all providers in the chain."""
        return {
            "providers": [
                {
                    "id": p.id,
                    "name": p.name,
                    "available": p.is_available(),
                    "diagnostics": p.diagnostics(),
                }
                for p in self.providers
            ],
            "current_provider": self.current_provider.id if self.current_provider else None,
        }
    
    def reset(self):
        """Reset the chain to start from the first provider."""
        self._current_provider_index = 0


def create_stt_fallback_chain(config: Dict[str, Any], providers: Dict[str, STTProvider]) -> STTFallbackChain:
    """Create an STT fallback chain from configuration."""
    # Get fallback order from config
    fallback_order = config.get("stt", {}).get("fallback_order", [])
    
    if not fallback_order:
        # Default order: primary provider first, then fallbacks
        primary = config.get("stt", {}).get("provider", "insanely_fast_whisper")
        fallback = config.get("stt", {}).get("fallback_provider", "groq")
        
        fallback_order = [primary, fallback]
    
    # Build provider list
    provider_list = []
    for provider_id in fallback_order:
        if provider_id in providers:
            provider_list.append(providers[provider_id])
    
    if not provider_list:
        raise STTError("No STT providers configured")
    
    return STTFallbackChain(provider_list)
