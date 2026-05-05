import time
from typing import Optional
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import ContextError
from ghosttype.packages.ghosttype_desktop.history.chunks import ChunkHistory


class LastOutputContextProvider:
    """Provides last output as context."""
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._history = ChunkHistory(config)
    
    def is_available(self) -> bool:
        """Check if last output provider is available."""
        return True  # Always available if history is available
    
    def get(self) -> Optional[str]:
        """Get last output."""
        chunk = self._history.get_last()
        if chunk and chunk.text:
            return chunk.text
        return None
    
    def diagnostics(self) -> dict:
        """Get diagnostics."""
        return {
            "available": self.is_available(),
            "history_size": self._history.count(),
        }
