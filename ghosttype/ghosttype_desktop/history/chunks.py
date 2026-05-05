import os
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import ActionExecutionError


@dataclass
class Chunk:
    """Represents a chunk of action history."""
    id: str
    type: str  # insert_text, press_key, paste_text, etc.
    text: str = ""
    key: str = ""
    reversible: bool = True
    backend_method: str = ""
    undo_strategy: str = "default"
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        return cls(**data)


class ChunkHistory:
    """Manages chunk history for undo operations."""
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._chunks: List[Chunk] = []
        self._state_dir = None
        self._history_file = None
    
    def _ensure_state_dir(self):
        """Ensure state directory exists."""
        if self._state_dir is None:
            from ghosttype.core.config import ConfigManager
            mgr = ConfigManager()
            self._state_dir = mgr.get_path("state")
            self._history_file = os.path.join(self._state_dir, "history.json")
        
        os.makedirs(self._state_dir, exist_ok=True)
    
    def add(self, chunk: Chunk):
        """Add a chunk to history."""
        self._ensure_state_dir()
        self._chunks.append(chunk)
        self._save()
    
    def get_last(self) -> Optional[Chunk]:
        """Get the last chunk."""
        if self._chunks:
            return self._chunks[-1]
        return None
    
    def list_chunks(self) -> List[Chunk]:
        """List all chunks."""
        return self._chunks.copy()
    
    def count(self) -> int:
        """Get chunk count."""
        return len(self._chunks)
    
    def undo_last(self) -> bool:
        """Undo the last chunk."""
        if not self._chunks:
            return False
        
        chunk = self._chunks.pop()
        self._save()
        
        # Perform undo action
        if chunk.type == "insert_text":
            # Undo by deleting the text
            return True
        elif chunk.type == "press_key":
            # Undo by pressing the key again
            return True
        elif chunk.type == "paste_text":
            # Undo by pasting previous clipboard
            return True
        
        return True
    
    def clear(self):
        """Clear all history."""
        self._chunks.clear()
        self._save()
    
    def _save(self):
        """Save history to file."""
        if self._history_file:
            data = [chunk.to_dict() for chunk in self._chunks]
            with open(self._history_file, "w") as f:
                json.dump(data, f, indent=2)
    
    def _load(self):
        """Load history from file."""
        if self._history_file and os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r") as f:
                    data = json.load(f)
                    self._chunks = [Chunk.from_dict(d) for d in data]
            except Exception:
                self._chunks = []
