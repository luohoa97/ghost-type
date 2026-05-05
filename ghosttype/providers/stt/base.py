from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from ghosttype.core.errors import STTError


class STTProvider(ABC):
    """Base class for STT providers."""
    
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
    def transcribe(self, audio: bytes, options: Optional[Dict[str, Any]] = None) -> str:
        """Transcribe audio to text."""
        pass
    
    def supports_streaming(self) -> bool:
        """Check if streaming is supported."""
        return False
    
    def supports_local(self) -> bool:
        """Check if local processing is supported."""
        return False
    
    def supports_remote(self) -> bool:
        """Check if remote processing is supported."""
        return False
