import os
from typing import Optional, Dict, Any
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import LLMError, ProviderNotConfigured, ProviderUnavailable
from ghosttype.providers.llm.base import LLMProvider


class OpenRouterProvider(LLMProvider):
    """LLM provider using OpenRouter API."""
    
    def __init__(self, config: Optional[GhostTypeConfig] = None):
        self.config = config
        self._api_key = None
        self._model = "openai/gpt-4o-mini"
        self._temperature = 0.0
        self._base_url = "https://openrouter.ai/api/v1"
    
    @property
    def id(self) -> str:
        return "openrouter"
    
    @property
    def name(self) -> str:
        return "OpenRouter"
    
    def _load_config(self):
        """Load configuration."""
        if self.config:
            self._model = self.config.llm.strong.model if hasattr(self.config.llm, "strong") else self._model
            self._api_key = self._resolve_api_key()
    
    def _resolve_api_key(self) -> Optional[str]:
        """Resolve API key from config or environment."""
        if not self.config:
            return os.environ.get("OPENROUTER_API_KEY")
        
        api_key = self.config.secrets.openrouter_api_key
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
            "base_url": self._base_url,
            "api_key_set": bool(self._api_key),
            "requires_api_key": True,
        }
    
    def complete(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a request."""
        self._load_config()
        
        if not self._api_key:
            raise ProviderNotConfigured("OPENROUTER_API_KEY not set")
        
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
            
            # Make request to OpenRouter API
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/ghosttype/ghosttype",
                "X-Title": "GhostType",
            }
            
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise LLMError(f"OpenRouter API error: {response.status_code} - {response.text}")
            
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
    
    def supports_json_schema(self) -> bool:
        return True
    
    def supports_streaming(self) -> bool:
        return True
