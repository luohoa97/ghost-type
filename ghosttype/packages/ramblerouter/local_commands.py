from typing import Dict, Any, List, Optional
from ghosttype.core.errors import RouterError


class LocalCommands:
    """Handles local command execution."""
    
    def __init__(self):
        self._commands = self._build_commands()
    
    def _build_commands(self) -> Dict[str, Dict[str, Any]]:
        """Build command map."""
        return {
            "new line": {
                "action": "press_key",
                "key": "Enter",
            },
            "tab": {
                "action": "press_key",
                "key": "Tab",
            },
            "backspace": {
                "action": "press_key",
                "key": "BackSpace",
            },
            "scrap that": {
                "action": "undo_last_chunk",
            },
            "scratch that": {
                "action": "undo_last_chunk",
            },
            "undo that": {
                "action": "undo_last_chunk",
            },
            "delete last word": {
                "action": "delete_last_word",
            },
        }
    
    def get_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Get command for text."""
        text_lower = text.lower().strip()
        return self._commands.get(text_lower)
    
    def execute(self, command: Dict[str, Any]) -> bool:
        """Execute a command."""
        action = command.get("action")
        
        if action == "press_key":
            return True  # Would press key via backend
        elif action == "undo_last_chunk":
            return True  # Would undo via history
        elif action == "delete_last_word":
            return True  # Would delete word via backend
        
        return False
