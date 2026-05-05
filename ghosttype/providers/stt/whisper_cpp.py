import os
import subprocess
from typing import Optional, Dict, Any
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import STTError, ProviderUnavailable, ProviderNotConfigured
from ghosttype.providers.stt.base import STTProvider


class WhisperCppProvider(STTProvider):
    """STT provider using Whisper.cpp (local)."""
    
    def __init__(self, config: Optional[GhostTypeConfig] = None):
        self.config = config
        self._binary = "whisper-cli"
        self._model = None
        self._available = None
    
    @property
    def id(self) -> str:
        return "whisper-cpp"
    
    @property
    def name(self) -> str:
        return "Whisper.cpp"
    
    def _check_binary(self) -> bool:
        """Check if whisper-cli is available."""
        import shutil
        return bool(shutil.which(self._binary))
    
    def _check_model(self) -> bool:
        """Check if model file exists."""
        if not self._model:
            return False
        
        import os
        return os.path.exists(self._model)
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        if self._available is not None:
            return self._available
        
        has_binary = self._check_binary()
        has_model = self._check_model()
        
        self._available = has_binary and has_model
        return self._available
    
    def diagnostics(self) -> Dict[str, Any]:
        """Get provider diagnostics."""
        import shutil
        
        return {
            "id": self.id,
            "name": self.name,
            "available": self.is_available(),
            "binary": self._binary,
            "binary_found": bool(shutil.which(self._binary)),
            "model": self._model,
            "model_exists": self._check_model() if self._model else False,
            "requires_binary": True,
            "requires_model": True,
        }
    
    def set_model(self, model_path: str):
        """Set model file path."""
        self._model = model_path
    
    def transcribe(self, audio: bytes, options: Optional[Dict[str, Any]] = None) -> str:
        """Transcribe audio to text."""
        if not self.is_available():
            if not self._check_binary():
                raise ProviderUnavailable(
                    "whisper-cli not found. "
                    "Install from: https://github.com/ggerganov/whisper.cpp"
                )
            if not self._check_model():
                raise ProviderNotConfigured(
                    "Whisper model not configured. "
                    "Set model path in config."
                )
        
        try:
            import tempfile
            import os
            
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio)
                audio_path = f.name
            
            try:
                # Run whisper-cli
                cmd = [self._binary, "-m", self._model, "-f", audio_path]
                
                if options and "language" in options:
                    cmd.extend(["-l", options["language"]])
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    raise STTError(f"Whisper failed: {result.stderr}")
                
                return result.stdout.strip()
                
            finally:
                os.unlink(audio_path)
                
        except subprocess.TimeoutExpired:
            raise STTError("Transcription timed out")
        except Exception as e:
            raise STTError(f"Transcription failed: {e}")
    
    def supports_streaming(self) -> bool:
        return False
    
    def supports_local(self) -> bool:
        return True
    
    def supports_remote(self) -> bool:
        return False
