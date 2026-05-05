import os
from typing import Optional, Dict, Any
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import STTError, ProviderUnavailable, DependencyMissing
from ghosttype.providers.stt.base import STTProvider


class InsanelyFastWhisperProvider(STTProvider):
    """STT provider using Insanely Fast Whisper (local)."""
    
    def __init__(self, config: Optional[GhostTypeConfig] = None):
        self.config = config
        self._model = "openai/whisper-large-v3"
        self._device = "auto"
        self._batch_size = 16
        self._dtype = "float16"
        self._flash_attention = True
        self._available = None
    
    @property
    def id(self) -> str:
        return "insanely-fast-whisper"
    
    @property
    def name(self) -> str:
        return "Insanely Fast Whisper"
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        try:
            import torch
            import transformers
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
        import torch
        
        return {
            "id": self.id,
            "name": self.name,
            "available": self.is_available(),
            "model": self._model,
            "device": self._device,
            "batch_size": self._batch_size,
            "dtype": self._dtype,
            "flash_attention": self._flash_attention,
            "torch_available": "✅" if self._check_dependencies() else "❌",
            "cuda_available": "✅" if torch.cuda.is_available() else "❌",
            "requires_dependencies": True,
        }
    
    def transcribe(self, audio: bytes, options: Optional[Dict[str, Any]] = None) -> str:
        """Transcribe audio to text."""
        if not self.is_available():
            raise ProviderUnavailable(
                "Insanely Fast Whisper is not available. "
                "Install dependencies: uv add 'faster-whisper[torch]'"
            )
        
        try:
            from faster_whisper import WhisperModel
            
            # Load model
            model = WhisperModel(
                self._model,
                device=self._device,
                compute_type=self._dtype,
                flash_attention=self._flash_attention,
            )
            
            # Transcribe
            segments, info = model.transcribe(
                audio,
                language=options.get("language", self._language) if options else self._language,
                batch_size=self._batch_size,
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
