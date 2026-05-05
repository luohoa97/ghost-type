import os
import base64
from typing import Optional, Dict, Any
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import STTError, ProviderNotConfigured, ProviderUnavailable
from ghosttype.providers.stt.base import STTProvider


class GroqWhisperProvider(STTProvider):
    """STT provider using Groq Whisper API."""
    
    def __init__(self, config: Optional[GhostTypeConfig] = None):
        self.config = config
        self._api_key = None
        self._model = "whisper-large-v3"
        self._language = "auto"
        self._temperature = 0.0
    
    @property
    def id(self) -> str:
        return "groq-whisper"
    
    @property
    def name(self) -> str:
        return "Groq Whisper"
    
    def _load_config(self):
        """Load configuration."""
        if self.config:
            self._model = self.config.stt.model
            self._language = self.config.stt.language
            self._api_key = self._resolve_api_key()
    
    def _resolve_api_key(self) -> Optional[str]:
        """Resolve API key from config or environment."""
        if not self.config:
            return os.environ.get("GROQ_API_KEY")
        
        api_key = self.config.secrets.groq_api_key
        if api_key.startswith("env:"):
            env_key = api_key.split(":", 1)[1]
            return os.environ.get(env_key)
        return api_key
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        self._load_config()
        
        if not self._api_key:
            return False
        
        try:
            import httpx
            return True
        except ImportError:
            return False
    
    def diagnostics(self) -> Dict[str, Any]:
        """Get provider diagnostics."""
        self._load_config()
        
        return {
            "id": self.id,
            "name": self.name,
            "available": self.is_available(),
            "model": self._model,
            "language": self._language,
            "api_key_set": bool(self._api_key),
            "requires_api_key": True,
        }
    
    def transcribe(self, audio: bytes, options: Optional[Dict[str, Any]] = None) -> str:
        """Transcribe audio to text."""
        self._load_config()
        
        if not self._api_key:
            raise ProviderNotConfigured("GROQ_API_KEY not set")
        
        if options:
            if "model" in options:
                self._model = options["model"]
            if "language" in options:
                self._language = options["language"]
            if "temperature" in options:
                self._temperature = options["temperature"]
        
        try:
            import httpx
            import json
            
            # Encode audio as base64
            audio_base64 = base64.b64encode(audio).decode("utf-8")
            
            # Prepare request
            data = {
                "model": self._model,
                "language": self._language,
                "temperature": self._temperature,
                "file": audio_base64,
            }
            
            # Make request to Groq API
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            
            response = httpx.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                json=data,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise STTError(f"Groq API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("text", "")
            
        except httpx.RequestError as e:
            raise STTError(f"Failed to transcribe: {e}")
        except Exception as e:
            raise STTError(f"Transcription failed: {e}")
    
    def supports_streaming(self) -> bool:
        return False
    
    def supports_local(self) -> bool:
        return False
    
    def supports_remote(self) -> bool:
        return True
