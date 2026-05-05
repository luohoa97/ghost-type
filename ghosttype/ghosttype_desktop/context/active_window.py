import time
from typing import Optional, Dict, Any
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import ContextError
from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry


class ActiveWindowContextProvider:
    """Provides active window information as context."""
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._backend = DesktopRegistry.detect_best_backend()
    
    def is_available(self) -> bool:
        """Check if active window provider is available."""
        caps = self._backend.capabilities()
        return any(c.value == "active_window" for c in caps)
    
    def get(self) -> Optional[Dict[str, Any]]:
        """Get active window information."""
        if not self.is_available():
            raise ContextError("Active window provider not available")
        
        return self._backend.get_active_window()
    
    def diagnostics(self) -> dict:
        """Get diagnostics."""
        return {
            "available": self.is_available(),
            "backend": self._backend.get_name(),
            "capabilities": [c.value for c in self._backend.capabilities()],
        }
