import time
from typing import Optional
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import ContextError
from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry


class SelectedTextContextProvider:
    """Provides selected text as context."""
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._backend = DesktopRegistry.detect_best_backend()
    
    def is_available(self) -> bool:
        """Check if selected text provider is available."""
        caps = self._backend.capabilities()
        return any(c.value == "selected_text" for c in caps)
    
    def get(self) -> Optional[str]:
        """Get selected text."""
        if not self.is_available():
            raise ContextError("Selected text provider not available")
        
        return self._backend.get_selected_text()
    
    def diagnostics(self) -> dict:
        """Get diagnostics."""
        return {
            "available": self.is_available(),
            "backend": self._backend.get_name(),
            "capabilities": [c.value for c in self._backend.capabilities()],
        }
