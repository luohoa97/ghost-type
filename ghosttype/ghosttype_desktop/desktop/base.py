from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class Capability(Enum):
    GLOBAL_HOTKEY = "global_hotkey"
    KEY_DOWN_UP = "key_down_up"
    PASTE_TEXT = "paste_text"
    TYPE_TEXT = "type_text"
    PRESS_KEY = "press_key"
    READ_CLIPBOARD = "read_clipboard"
    WRITE_CLIPBOARD = "write_clipboard"
    SELECTED_TEXT = "selected_text"
    ACTIVE_WINDOW = "active_window"
    SCREENSHOT = "screenshot"
    OVERLAY = "overlay"
    NOTIFICATIONS = "notifications"

class DesktopBackend(ABC):
    @abstractmethod
    def detect(self) -> bool:
        """Detects if this backend is compatible with the current environment."""
        pass

    @abstractmethod
    def capabilities(self) -> List[Capability]:
        """Returns the list of capabilities supported by this backend."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Returns the name of the backend."""
        pass

    @abstractmethod
    def score(self) -> int:
        """Returns a score representing the quality of support for this backend."""
        pass

    @abstractmethod
    def diagnostics(self) -> Dict[str, Any]:
        """Returns diagnostic information about the backend and its tools."""
        pass

    # Basic desktop operations
    @abstractmethod
    def paste_text(self, text: str): pass

    @abstractmethod
    def type_text(self, text: str): pass

    @abstractmethod
    def press_key(self, key: str): pass

    @abstractmethod
    def read_clipboard(self) -> Optional[str]: pass

    @abstractmethod
    def write_clipboard(self, text: str): pass

    @abstractmethod
    def get_selected_text(self) -> Optional[str]: pass

    @abstractmethod
    def get_active_window(self) -> Dict[str, Any]: pass

    @abstractmethod
    def screenshot(self) -> Optional[bytes]: pass

    @abstractmethod
    def show_overlay(self, message: str): pass

    @abstractmethod
    def notify(self, title: str, message: str): pass
