import os
import socket
import threading
from typing import List, Optional, Dict, Any
from .base import DesktopBackend, Capability
from ghosttype.core.errors import DesktopBackendError


class GnomeExtensionBackend(DesktopBackend):
    """Desktop backend for GNOME Shell extension bridge."""
    
    def __init__(self):
        self._detected = False
        self._socket_path: Optional[str] = None
        self._connected = False
    
    def detect(self) -> bool:
        """Detect GNOME Shell extension availability."""
        # Check for GNOME extension socket
        xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000")
        socket_path = os.path.join(xdg_runtime, "ghosttype-gnome.sock")
        
        if os.path.exists(socket_path):
            self._socket_path = socket_path
            self._detected = True
            return True
        
        # Alternative: check if GNOME extension is installed
        # This would require checking dconf or similar
        return False
    
    def get_name(self) -> str:
        return "GNOME_Extension"
    
    def capabilities(self) -> List[Capability]:
        caps = []
        
        # GNOME extension can provide additional capabilities
        if self._detected:
            caps.extend([
                Capability.ACTIVE_WINDOW,
                Capability.OVERLAY,
                Capability.NOTIFICATIONS
            ])
        
        return caps
    
    def score(self) -> int:
        """Score GNOME extension backend."""
        if not self._detected:
            return 0
        
        return 80  # High score for GNOME extension
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "session_type": "wayland",
            "desktop_environment": "gnome",
            "extension_socket": self._socket_path,
            "connected": self._connected
        }
    
    def connect(self) -> bool:
        """Connect to GNOME extension socket."""
        if not self._socket_path or self._connected:
            return self._connected
        
        try:
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(self._socket_path)
            self._connected = True
            return True
        except (socket.error, FileNotFoundError):
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from GNOME extension socket."""
        if self._connected and hasattr(self, '_socket'):
            try:
                self._socket.close()
            except:
                pass
        self._connected = False
    
    def _send_command(self, command: str) -> Optional[str]:
        """Send a command to the GNOME extension."""
        if not self.connect():
            return None
        
        try:
            self._socket.sendall(command.encode())
            response = self._socket.recv(4096).decode()
            return response
        except (socket.error, ConnectionError):
            self._connected = False
            return None
    
    def paste_text(self, text: str):
        """Paste text via GNOME extension."""
        if not self.connect():
            # Fallback to clipboard
            from .generic import GenericClipboardBackend
            fallback = GenericClipboardBackend()
            fallback.paste_text(text)
            return
        
        try:
            self._send_command(f"paste:{text}")
        except Exception as e:
            raise DesktopBackendError(f"Failed to paste via extension: {e}")
    
    def type_text(self, text: str):
        """Type text via GNOME extension."""
        if not self.connect():
            raise DesktopBackendError("GNOME extension not available")
        
        try:
            self._send_command(f"type:{text}")
        except Exception as e:
            raise DesktopBackendError(f"Failed to type via extension: {e}")
    
    def press_key(self, key: str):
        """Press a key via GNOME extension."""
        if not self.connect():
            raise DesktopBackendError("GNOME extension not available")
        
        try:
            self._send_command(f"key:{key}")
        except Exception as e:
            raise DesktopBackendError(f"Failed to press key via extension: {e}")
    
    def read_clipboard(self) -> Optional[str]:
        """Read clipboard via GNOME extension."""
        if not self.connect():
            return None
        
        try:
            response = self._send_command("clipboard:get")
            return response if response else None
        except Exception:
            return None
    
    def write_clipboard(self, text: str):
        """Write text to clipboard via GNOME extension."""
        if not self.connect():
            raise DesktopBackendError("GNOME extension not available")
        
        try:
            self._send_command(f"clipboard:set:{text}")
        except Exception as e:
            raise DesktopBackendError(f"Failed to write clipboard via extension: {e}")
    
    def get_selected_text(self) -> Optional[str]:
        """Get selected text via GNOME extension."""
        if not self.connect():
            return None
        
        try:
            response = self._send_command("selection:get")
            return response if response else None
        except Exception:
            return None
    
    def get_active_window(self) -> Dict[str, Any]:
        """Get active window info via GNOME extension."""
        if not self.connect():
            return {}
        
        try:
            response = self._send_command("window:active")
            if response:
                # Parse JSON response
                import json
                return json.loads(response)
            return {}
        except Exception:
            return {}
    
    def screenshot(self) -> Optional[bytes]:
        """Take screenshot via GNOME extension."""
        if not self.connect():
            return None
        
        try:
            response = self._send_command("screenshot:active")
            if response:
                # Response would be base64 encoded
                import base64
                return base64.b64decode(response)
            return None
        except Exception:
            return None
    
    def show_overlay(self, message: str):
        """Show overlay via GNOME extension."""
        if not self.connect():
            from .generic import GenericClipboardBackend
            fallback = GenericClipboardBackend()
            fallback.notify("GhostType", message)
            return
        
        try:
            self._send_command(f"overlay:show:{message}")
        except Exception:
            from .generic import GenericClipboardBackend
            fallback = GenericClipboardBackend()
            fallback.notify("GhostType", message)
    
    def notify(self, title: str, message: str):
        """Show notification via GNOME extension."""
        if not self.connect():
            from .generic import GenericClipboardBackend
            fallback = GenericClipboardBackend()
            fallback.notify(title, message)
            return
        
        try:
            self._send_command(f"notify:{title}:{message}")
        except Exception:
            from .generic import GenericClipboardBackend
            fallback = GenericClipboardBackend()
            fallback.notify(title, message)
