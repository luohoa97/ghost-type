import os
from typing import List
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import ContextError


class VocabularyContextProvider:
    """Provides vocabulary words as context."""
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._vocabulary_path = None
    
    def is_available(self) -> bool:
        """Check if vocabulary provider is available."""
        return True  # Always available, may be empty
    
    def get(self) -> List[str]:
        """Get vocabulary words."""
        words = []
        
        # Try to load from vocabulary file
        if self._vocabulary_path and os.path.exists(self._vocabulary_path):
            try:
                with open(self._vocabulary_path, "r") as f:
                    words = [line.strip() for line in f if line.strip()]
            except Exception:
                pass
        
        return words
    
    def set_path(self, path: str):
        """Set vocabulary file path."""
        self._vocabulary_path = path
    
    def diagnostics(self) -> dict:
        """Get diagnostics."""
        return {
            "available": self.is_available(),
            "vocabulary_path": self._vocabulary_path,
            "word_count": len(self.get()),
        }
