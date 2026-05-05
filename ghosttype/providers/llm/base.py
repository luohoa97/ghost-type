from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from ghosttype.core.errors import LLMError


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Provider ID."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass
    
    @abstractmethod
    def diagnostics(self) -> Dict[str, Any]:
        """Get provider diagnostics."""
        pass
    
    @abstractmethod
    def complete(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a request."""
        pass
    
    def stream_complete(self, request: Dict[str, Any]):
        """Stream completion results."""
        raise NotImplementedError("Streaming not supported")
    
    def supports_json_schema(self) -> bool:
        """Check if JSON schema is supported."""
        return True
    
    def supports_streaming(self) -> bool:
        """Check if streaming is supported."""
        return False
