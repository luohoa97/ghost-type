import time
from typing import List, Dict, Any, Optional
from ghosttype.core.errors import ActionExecutionError, DesktopBackendError
from ghosttype.packages.ghosttype_desktop.history.chunks import ChunkHistory, Chunk


class ActionExecutor:
    """Executes actions using the desktop backend."""
    
    def __init__(self, backend):
        self.backend = backend
        self._history = None  # Will be initialized on first use
    
    def _get_history(self) -> ChunkHistory:
        """Get or create history manager."""
        if self._history is None:
            from ghosttype.core.config import ConfigManager
            config = ConfigManager()
            config.load()
            self._history = ChunkHistory(config.config)
        return self._history
    
    def execute_sequence(self, actions: List[Dict[str, Any]]):
        """Execute a sequence of actions."""
        for action in actions:
            self.execute(action)
    
    def execute(self, action: Dict[str, Any]):
        """Execute a single action."""
        action_type = action.get("type")
        
        if action_type == "insert_text":
            self._insert_text(action)
        elif action_type == "replace_selection":
            self._replace_selection(action)
        elif action_type == "copy_to_clipboard":
            self._copy_to_clipboard(action)
        elif action_type == "paste_text":
            self._paste_text(action)
        elif action_type == "type_text":
            self._type_text(action)
        elif action_type == "press_key":
            self._press_key(action)
        elif action_type == "undo_last_chunk":
            self._undo_last_chunk(action)
        elif action_type == "delete_last_word":
            self._delete_last_word(action)
        elif action_type == "show_overlay":
            self._show_overlay(action)
        elif action_type == "ask_confirmation":
            self._ask_confirmation(action)
        elif action_type == "route_to_strong_llm":
            self._route_to_strong_llm(action)
        elif action_type == "route_to_agent":
            self._route_to_agent(action)
        else:
            raise ActionExecutionError(f"Unknown action type: {action_type}")
    
    def _insert_text(self, action: Dict[str, Any]):
        """Insert text at cursor position."""
        text = action.get("text", "")
        
        # Try type_text first, fallback to paste
        try:
            self.backend.type_text(text)
            self._get_history().add(Chunk(
                id=str(uuid.uuid4()),
                type="insert_text",
                text=text,
                reversible=True,
                backend_method="type_text"
            ))
        except DesktopBackendError:
            # Fallback to paste
            self.backend.paste_text(text)
            self._get_history().add(Chunk(
                id=str(uuid.uuid4()),
                type="paste_text",
                text=text,
                reversible=True,
                backend_method="paste_text"
            ))
    
    def _replace_selection(self, action: Dict[str, Any]):
        """Replace selected text."""
        # First get selected text
        selected = self.backend.get_selected_text()
        
        # Insert new text
        text = action.get("text", "")
        self.backend.type_text(text)
        
        self._get_history().add(Chunk(
            id=str(uuid.uuid4()),
            type="replace_selection",
            text=text,
            reversible=True,
            backend_method="type_text"
        ))
    
    def _copy_to_clipboard(self, action: Dict[str, Any]):
        """Copy text to clipboard."""
        text = action.get("text", "")
        self.backend.write_clipboard(text)
        
        self._get_history().add(Chunk(
            id=str(uuid.uuid4()),
            type="copy_to_clipboard",
            text=text,
            reversible=False,
            backend_method="write_clipboard"
        ))
    
    def _paste_text(self, action: Dict[str, Any]):
        """Paste text from clipboard."""
        self.backend.paste_text("")
        
        self._get_history().add(Chunk(
            id=str(uuid.uuid4()),
            type="paste_text",
            text="",
            reversible=True,
            backend_method="paste_text"
        ))
    
    def _type_text(self, action: Dict[str, Any]):
        """Type text directly."""
        text = action.get("text", "")
        self.backend.type_text(text)
        
        self._get_history().add(Chunk(
            id=str(uuid.uuid4()),
            type="type_text",
            text=text,
            reversible=True,
            backend_method="type_text"
        ))
    
    def _press_key(self, action: Dict[str, Any]):
        """Press a key."""
        key = action.get("key", "")
        self.backend.press_key(key)
        
        self._get_history().add(Chunk(
            id=str(uuid.uuid4()),
            type="press_key",
            key=key,
            reversible=True,
            backend_method="press_key"
        ))
    
    def _undo_last_chunk(self, action: Dict[str, Any]):
        """Undo last chunk."""
        self._get_history().undo_last()
        
        self._get_history().add(Chunk(
            id=str(uuid.uuid4()),
            type="undo_last_chunk",
            reversible=True,
            backend_method="undo"
        ))
    
    def _delete_last_word(self, action: Dict[str, Any]):
        """Delete last word."""
        # Press Ctrl+Backspace
        self.backend.press_key("ctrl+backspace")
        
        self._get_history().add(Chunk(
            id=str(uuid.uuid4()),
            type="delete_last_word",
            reversible=True,
            backend_method="press_key"
        ))
    
    def _show_overlay(self, action: Dict[str, Any]):
        """Show overlay message."""
        message = action.get("message", "")
        self.backend.show_overlay(message)
    
    def _ask_confirmation(self, action: Dict[str, Any]):
        """Ask user for confirmation."""
        message = action.get("message", "")
        # In CLI mode, we'd prompt the user
        print(f"Confirmation required: {message}")
        # For now, auto-accept
        return True
    
    def _route_to_strong_llm(self, action: Dict[str, Any]):
        """Route to strong LLM."""
        # This would trigger the strong LLM route
        print("Routing to strong LLM")
        return True
    
    def _route_to_agent(self, action: Dict[str, Any]):
        """Route to agent."""
        # This would trigger the agent route
        print("Routing to agent")
        return True
