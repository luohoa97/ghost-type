"""UI button input provider for GhostType."""
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from threading import Thread, Event

from ghosttype.core.errors import CapabilityUnavailable


@dataclass
class UIButtonEvent:
    """Represents a UI button event."""
    button_id: str
    state: str  # "pressed" or "released"
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class UIButtonProvider:
    """Input provider for UI buttons (placeholder for GUI integration)."""
    
    def __init__(self):
        self._running = False
        self._event_callback: Optional[Callable[[UIButtonEvent], None]] = None
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        
        # Check if GUI dependencies are available
        self._has_gui = self._check_gui_dependencies()
    
    def _check_gui_dependencies(self) -> bool:
        """Check if GUI dependencies are available."""
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
            return True
        except (ImportError, ValueError):
            return False
    
    def start_listening(self, callback: Callable[[UIButtonEvent], None]):
        """Start listening for UI button events."""
        if not self._has_gui:
            raise CapabilityUnavailable(
                "GUI dependencies not available. "
                "Install libadwaita: sudo apt install libadwaita-1-0"
            )
        
        self._event_callback = callback
        self._running = True
        self._stop_event.clear()
        
        self._thread = Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
    
    def _listen_loop(self):
        """Main listening loop."""
        # In a real implementation, this would connect to GTK signals
        # For now, this is a placeholder that waits for external events
        import time
        
        while self._running and not self._stop_event.is_set():
            time.sleep(0.1)
    
    def stop_listening(self):
        """Stop listening for events."""
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
    
    def is_available(self) -> bool:
        """Check if UI button provider is available."""
        return self._has_gui
    
    def trigger_button(self, button_id: str, state: str = "pressed"):
        """Manually trigger a button event."""
        if self._event_callback:
            event = UIButtonEvent(button_id=button_id, state=state)
            self._event_callback(event)
    
    def diagnostics(self) -> Dict[str, Any]:
        """Get diagnostics for UI button provider."""
        return {
            "available": self.is_available(),
            "gui_dependencies": self._has_gui,
            "running": self._running,
        }


class MockUIButtonProvider(UIButtonProvider):
    """Mock UI button provider for testing."""
    
    def __init__(self):
        super().__init__()
        self._events: list = []
    
    def trigger_button(self, button_id: str, state: str = "pressed"):
        """Trigger a button event and record it."""
        event = UIButtonEvent(button_id=button_id, state=state)
        self._events.append(event)
        
        if self._event_callback:
            self._event_callback(event)
    
    def get_events(self) -> list:
        """Get recorded events."""
        return self._events.copy()
    
    def clear_events(self):
        """Clear recorded events."""
        self._events.clear()
