import os
from typing import Optional, Dict, Any
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import STTError, ProviderUnavailable, DependencyMissing
from ghosttype.providers.stt.base import STTProvider


class FasterWhisperProvider(STTProvider):
    """STT provider using Faster Whisper (local)."""
    
    def __init__(self, config: Optional[GhostTypeConfig] = None):
        self.config = config
        self._model = "large-v3"
        self._device = "auto"
        self._compute_type = "int8"
        self._available = None
    
    @property
    def id(self) -> str:
        return "faster-whisper"
    
    @property
    def name(self) -> str:
        return "Faster Whisper"
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        try:
            import faster_whisper
            return True
        except ImportError:
            return False
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        if self._available is not None:
            return self._available
        
        self._available = self._check_dependencies()
        return self._available
    
    def diagnostics(self) -> Dict[str, Any]:
        """Get provider diagnostics."""
        return {
            "id": self.id,
            "name": self.name,
            "available": self.is_available(),
            "model": self._model,
            "device": self._device,
            "compute_type": self._compute_type,
            "requires_dependencies": True,
        }
    
    def transcribe(self, audio: bytes, options: Optional[Dict[str, Any]] = None) -> str:
        """Transcribe audio to text."""
        if not self.is_available():
            raise ProviderUnavailable(
                "Faster Whisper is not available. "
                "Install dependencies: uv add faster-whisper"
            )
        
        try:
            from faster_whisper import WhisperModel
            
            # Load model
            model = WhisperModel(
                self._model,
                device=self._device,
                compute_type=self._compute_type,
            )
            
            # Transcribe
            segments, info = model.transcribe(
                audio,
                language=options.get("language", self._language) if options else self._language,
            )
            
            # Collect text
            text = ""
            for segment in segments:
                text += segment.text
            
            return text.strip()
            
        except Exception as e:
            raise STTError(f"Transcription failed: {e}")
    
    def supports_streaming(self) -> bool:
        return False
    
    def supports_local(self) -> bool:
        return True
    
    def supports_remote(self) -> bool:
        return False
