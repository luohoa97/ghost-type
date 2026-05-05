import os
from typing import Optional, Dict, Any
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import LLMError, ProviderNotConfigured, ProviderUnavailable
from ghosttype.providers.llm.base import LLMProvider


class GroqProvider(LLMProvider):
    """LLM provider using Groq API."""
    
    def __init__(self, config: Optional[GhostTypeConfig] = None):
        self.config = config
        self._api_key = None
        self._model = "llama-3.1-8b-instant"
        self._temperature = 0.0
    
    @property
    def id(self) -> str:
        return "groq"
    
    @property
    def name(self) -> str:
        return "Groq"
    
    def _load_config(self):
        """Load configuration."""
        if self.config:
            self._model = self.config.llm.fast.model if hasattr(self.config.llm, "fast") else self._model
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
            "api_key_set": bool(self._api_key),
            "requires_api_key": True,
        }
    
    def complete(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a request."""
        self._load_config()
        
        if not self._api_key:
            raise ProviderNotConfigured("GROQ_API_KEY not set")
        
        try:
            import httpx
            import json
            
            # Prepare request
            messages = request.get("messages", [])
            
            data = {
                "model": self._model,
                "messages": messages,
                "temperature": request.get("temperature", self._temperature),
            }
            
            # Add JSON schema if requested
            if request.get("response_format") == "json":
                data["response_format"] = {"type": "json_object"}
            
            # Make request to Groq API
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise LLMError(f"Groq API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": result["model"],
                "usage": result.get("usage", {}),
            }
            
        except httpx.RequestError as e:
            raise LLMError(f"Failed to complete: {e}")
        except Exception as e:
            raise LLMError(f"Completion failed: {e}")
    
    def stream_complete(self, request: Dict[str, Any]):
        """Stream completion results."""
        raise NotImplementedError("Streaming not supported for Groq provider")
    
    def supports_json_schema(self) -> bool:
        return True
    
    def supports_streaming(self) -> bool:
        return False
