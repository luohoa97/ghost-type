import os
from typing import Optional, Dict, Any
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import LLMError, ProviderUnavailable, ProviderNotConfigured
from ghosttype.providers.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """LLM provider using local Ollama."""
    
    def __init__(self, config: Optional[GhostTypeConfig] = None):
        self.config = config
        self._base_url = "http://localhost:11434"
        self._model = "llama3"
        self._temperature = 0.0
        self._available = None
    
    @property
    def id(self) -> str:
        return "ollama"
    
    @property
    def name(self) -> str:
        return "Ollama"
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        import httpx
        try:
            response = httpx.get(f"{self._base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_model(self) -> bool:
        """Check if model is available."""
        import httpx
        try:
            response = httpx.get(f"{self._base_url}/api/tags", timeout=5.0)
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            return any(m.get("name") == self._model for m in models)
        except Exception:
            return False
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        if self._available is not None:
            return self._available
        
        has_ollama = self._check_ollama()
        has_model = self._check_model()
        
        self._available = has_ollama and has_model
        return self._available
    
    def diagnostics(self) -> Dict[str, Any]:
        """Get provider diagnostics."""
        import httpx
        
        return {
            "id": self.id,
            "name": self.name,
            "available": self.is_available(),
            "base_url": self._base_url,
            "model": self._model,
            "ollama_running": self._check_ollama(),
            "model_available": self._check_model(),
            "requires_local_ollama": True,
        }
    
    def set_model(self, model: str):
        """Set model name."""
        self._model = model
        self._available = None  # Reset availability check
    
    def complete(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a request."""
        if not self.is_available():
            if not self._check_ollama():
                raise ProviderUnavailable(
                    "Ollama is not running. "
                    "Start Ollama: ollama serve"
                )
            if not self._check_model():
                raise ProviderNotConfigured(
                    f"Model '{self._model}' not found. "
                    f"Pull it with: ollama pull {self._model}"
                )
        
        try:
            import httpx
            import json
            
            # Prepare request
            messages = request.get("messages", [])
            
            data = {
                "model": self._model,
                "messages": messages,
                "temperature": request.get("temperature", self._temperature),
                "stream": False,
            }
            
            # Add JSON schema if requested
            if request.get("response_format") == "json":
                data["format"] = "json"
            
            # Make request to Ollama API
            response = httpx.post(
                f"{self._base_url}/api/chat",
                json=data,
                timeout=120.0
            )
            
            if response.status_code != 200:
                raise LLMError(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            return {
                "content": result["message"]["content"],
                "model": result["model"],
            }
            
        except httpx.RequestError as e:
            raise LLMError(f"Failed to complete: {e}")
        except Exception as e:
            raise LLMError(f"Completion failed: {e}")
    
    def supports_json_schema(self) -> bool:
        return True
    
    def supports_streaming(self) -> bool:
        return True
