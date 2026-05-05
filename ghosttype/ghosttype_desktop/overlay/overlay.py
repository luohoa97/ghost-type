from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import logging

from ghosttype.core.config import GhostTypeConfig


class OverlayState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    SHOWING_RESULT = "showing_result"
    ERROR = "error"
    LISTENING = "listening"


@dataclass
class OverlayEvent:
    state: OverlayState
    text: str = ""
    message: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class OverlayBackend(ABC):
    @abstractmethod
    def show(self, text: str, state: OverlayState):
        pass
    
    @abstractmethod
    def hide(self):
        pass
    
    @abstractmethod
    def update_state(self, state: OverlayState):
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass


class OverlayAbstraction:
    def __init__(
        self,
        config: GhostTypeConfig,
        backends: Optional[List[OverlayBackend]] = None,
    ):
        self.config = config
        self._backends: List[OverlayBackend] = backends or []
        self._current_backend: Optional[OverlayBackend] = None
        self._state = OverlayState.IDLE
        self._current_text = ""
        self._event_listeners: List[Callable[[OverlayEvent], None]] = []
        self._logger = logging.getLogger("ghosttype.overlay")
        
        self._select_backend()
    
    def _select_backend(self):
        for backend in self._backends:
            if backend.is_available():
                self._current_backend = backend
                self._logger.info(f"Selected overlay backend: {backend.get_name()}")
                return
        
        fallback = NotificationFallbackBackend()
        self._current_backend = fallback
        self._logger.info(f"Using fallback backend: {fallback.get_name()}")
    
    def add_backend(self, backend: OverlayBackend):
        self._backends.append(backend)
        if self._current_backend is None:
            self._select_backend()
    
    def show(self, text: str, state: Optional[OverlayState] = None):
        if state:
            self._state = state
        
        self._current_text = text
        
        if self._current_backend:
            self._current_backend.show(text, self._state)
        
        self._emit_event(OverlayEvent(
            state=self._state,
            text=text,
        ))
    
    def hide(self):
        self._state = OverlayState.IDLE
        self._current_text = ""
        
        if self._current_backend:
            self._current_backend.hide()
        
        self._emit_event(OverlayEvent(
            state=OverlayState.IDLE,
            message="Overlay hidden",
        ))
    
    def update_state(self, state: OverlayState, message: str = ""):
        self._state = state
        
        if self._current_backend:
            self._current_backend.update_state(state)
        
        self._emit_event(OverlayEvent(
            state=state,
            text=self._current_text,
            message=message,
        ))
    
    def set_recording(self, text: str = ""):
        self.show(text or "Recording...", OverlayState.RECORDING)
    
    def set_processing(self, text: str = ""):
        self.show(text or "Processing...", OverlayState.PROCESSING)
    
    def set_result(self, text: str):
        self.show(text, OverlayState.SHOWING_RESULT)
    
    def set_error(self, message: str):
        self.show(f"Error: {message}", OverlayState.ERROR)
    
    def set_listening(self, text: str = ""):
        self.show(text or "Listening...", OverlayState.LISTENING)
    
    def set_idle(self):
        self.hide()
    
    def on_event(self, listener: Callable[[OverlayEvent], None]):
        self._event_listeners.append(listener)
    
    def _emit_event(self, event: OverlayEvent):
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception as e:
                self._logger.error(f"Error in overlay event listener: {e}")
    
    def get_current_backend(self) -> Optional[OverlayBackend]:
        return self._current_backend
    
    def get_state(self) -> OverlayState:
        return self._state
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "current_backend": self._current_backend.get_name() if self._current_backend else None,
            "available_backends": [b.get_name() for b in self._backends if b.is_available()],
            "current_text": self._current_text,
        }


class RealGUIOverlayBackend(OverlayBackend):
    def __init__(self):
        self._state = OverlayState.IDLE
        self._window = None
        self._gtk_available = self._check_gtk()
    
    def _check_gtk(self) -> bool:
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            return True
        except (ImportError, ValueError):
            return False
    
    def show(self, text: str, state: OverlayState):
        if not self._gtk_available:
            return
        
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            
            from gi.repository import Gtk, Gdk, Adw
            
            if self._window is None:
                self._window = Gtk.Window()
                self._window.set_decorated(False)
                self._window.set_resizable(False)
                self._window.set_keep_above(True)
                
                screen = Gdk.Display.get_default().get_monitor(0)
                if screen:
                    geometry = screen.get_geometry()
                    width = min(400, geometry.width - 40)
                    self._window.set_default_size(width, 50)
                    self._window.move(
                        geometry.width - width - 20,
                        geometry.height - 80
                    )
                
                self._overlay_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                self._overlay_box.set_margin_top(8)
                self._overlay_box.set_margin_bottom(8)
                self._overlay_box.set_margin_start(12)
                self._overlay_box.set_margin_end(12)
                
                self._overlay_label = Gtk.Label()
                self._overlay_label.set_halign(Gtk.Align.START)
                self._overlay_label.set_valign(Gtk.Align.CENTER)
                self._overlay_label.set_wrap(True)
                self._overlay_box.append(self._overlay_label)
                
                self._window.set_child(self._overlay_box)
            
            self._overlay_label.set_text(text)
            self._state = state
            
            self._window.show()
            
        except Exception:
            self._gtk_available = False
    
    def hide(self):
        if self._window:
            self._window.hide()
        self._state = OverlayState.IDLE
    
    def update_state(self, state: OverlayState):
        self._state = state
    
    def is_available(self) -> bool:
        return self._gtk_available
    
    def get_name(self) -> str:
        return "gui_overlay"


class NotificationFallbackBackend(OverlayBackend):
    def __init__(self):
        self._state = OverlayState.IDLE
        self._notify_available = self._check_notify()
    
    def _check_notify(self) -> bool:
        try:
            import subprocess
            subprocess.run(["notify-send", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def show(self, text: str, state: OverlayState):
        if not self._notify_available:
            return
        
        try:
            import subprocess
            
            urgency = "low"
            if state == OverlayState.ERROR:
                urgency = "critical"
            elif state == OverlayState.RECORDING:
                urgency = "normal"
            
            icon = ""
            if state == OverlayState.RECORDING:
                icon = "audio-input-microphone"
            elif state == OverlayState.PROCESSING:
                icon = "emblem-synchronizing"
            elif state == OverlayState.ERROR:
                icon = "dialog-error"
            
            cmd = ["notify-send", "-u", urgency]
            if icon:
                cmd.extend(["-i", icon])
            cmd.extend(["GhostType", text])
            
            subprocess.Popen(cmd)
            
            self._state = state
            
        except Exception:
            self._notify_available = False
    
    def hide(self):
        self._state = OverlayState.IDLE
        if self._notify_available:
            try:
                import subprocess
                subprocess.run(["notify-send", "--close"], capture_output=True)
            except Exception:
                pass
    
    def update_state(self, state: OverlayState):
        self._state = state
    
    def is_available(self) -> bool:
        return self._notify_available
    
    def get_name(self) -> str:
        return "notification_fallback"


class TerminalPrintBackend(OverlayBackend):
    def __init__(self):
        self._state = OverlayState.IDLE
    
    def show(self, text: str, state: OverlayState):
        import sys
        
        line = f"\r[GhostType] {text}"
        sys.stdout.write(line)
        sys.stdout.flush()
        self._state = state
    
    def hide(self):
        import sys
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
        self._state = OverlayState.IDLE
    
    def update_state(self, state: OverlayState):
        self._state = state
    
    def is_available(self) -> bool:
        return True
    
    def get_name(self) -> str:
        return "terminal_print"


class LogBackend(OverlayBackend):
    def __init__(self):
        self._logger = logging.getLogger("ghosttype.overlay")
        self._state = OverlayState.IDLE
    
    def show(self, text: str, state: OverlayState):
        self._logger.info(f"[{state.value}] {text}")
        self._state = state
    
    def hide(self):
        self._logger.debug("Overlay hidden")
        self._state = OverlayState.IDLE
    
    def update_state(self, state: OverlayState):
        self._state = state
        self._logger.debug(f"Overlay state: {state.value}")
    
    def is_available(self) -> bool:
        return True
    
    def get_name(self) -> str:
        return "log"


def create_overlay(config: GhostTypeConfig) -> OverlayAbstraction:
    backends = [
        RealGUIOverlayBackend(),
        NotificationFallbackBackend(),
        TerminalPrintBackend(),
        LogBackend(),
    ]
    
    return OverlayAbstraction(config, backends)
