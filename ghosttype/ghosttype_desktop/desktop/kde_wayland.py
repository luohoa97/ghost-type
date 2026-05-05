import os
import shutil
import subprocess
from typing import List, Optional, Dict, Any
from .base import DesktopBackend, Capability
from ghosttype.core.errors import DesktopBackendError


class KDEWaylandBackend(DesktopBackend):
    """Desktop backend for KDE Wayland sessions."""
    
    def __init__(self):
        self._detected = False
        self._tools = {}
    
    def detect(self) -> bool:
        """Detect KDE Wayland session."""
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        
        # KDE Wayland detection
        if session_type == "wayland" and ("kde" in de or "plasma" in de):
            self._detected = True
            self._tools = find_kde_tools()
            return True
        
        return False
    
    def get_name(self) -> str:
        return "KDE_Wayland"
    
    def capabilities(self) -> List[Capability]:
        caps = []
        
        if self._tools.get("ydotool"):
            caps.extend([
                Capability.TYPE_TEXT,
                Capability.PRESS_KEY,
                Capability.KEY_DOWN_UP
            ])
        
        if self._tools.get("wl-copy") or self._tools.get("wl-paste"):
            caps.extend([
                Capability.READ_CLIPBOARD,
                Capability.WRITE_CLIPBOARD
            ])
        
        if self._tools.get("spectacle"):
            caps.append(Capability.SCREENSHOT)
        
        if self._tools.get("qdbus"):
            caps.extend([
                Capability.ACTIVE_WINDOW,
                Capability.NOTIFICATIONS
            ])
        
        if self._tools.get("ydotool"):
            caps.append(Capability.OVERLAY)
        
        return caps
    
    def score(self) -> int:
        """Score KDE Wayland backend."""
        if not self._detected:
            return 0
        
        score = 60  # Base score for KDE Wayland
        
        # Bonus for available tools
        if self._tools.get("ydotool"):
            score += 25
        if self._tools.get("wl-copy") or self._tools.get("wl-paste"):
            score += 15
        if self._tools.get("spectacle"):
            score += 10
        if self._tools.get("qdbus"):
            score += 10
        
        return min(score, 100)
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "session_type": "wayland",
            "desktop_environment": "kde",
            "display": os.environ.get("WAYLAND_DISPLAY"),
            "tools": self._tools
        }
    
    def paste_text(self, text: str):
        """Paste text using clipboard."""
        self.write_clipboard(text)
        
        if self._tools.get("ydotool"):
            try:
                subprocess.run(["ydotool", "key", "ctrl+v"], check=True)
            except subprocess.CalledProcessError as e:
                raise DesktopBackendError(f"Failed to paste: {e}")
        else:
            self.notify("GhostType", "Text copied to clipboard. Please paste manually (Ctrl+V).")
    
    def type_text(self, text: str):
        """Type text using ydotool."""
        if not self._tools.get("ydotool"):
            raise DesktopBackendError("ydotool not available")
        
        try:
            escaped_text = text.replace("\\", "\\\\").replace(" ", "\\ ")
            subprocess.run(["ydotool", "type", escaped_text], check=True)
        except subprocess.CalledProcessError as e:
            raise DesktopBackendError(f"Failed to type text: {e}")
    
    def press_key(self, key: str):
        """Press a key using ydotool."""
        if not self._tools.get("ydotool"):
            raise DesktopBackendError("ydotool not available")
        
        try:
            subprocess.run(["ydotool", "key", key], check=True)
        except subprocess.CalledProcessError as e:
            raise DesktopBackendError(f"Failed to press key: {e}")
    
    def read_clipboard(self) -> Optional[str]:
        """Read clipboard content."""
        if self._tools.get("wl-paste"):
            try:
                return subprocess.check_output(["wl-paste"], text=True)
            except subprocess.CalledProcessError:
                return None
        elif self._tools.get("wl-copy"):
            try:
                return subprocess.check_output(["wl-copy", "--print"], text=True)
            except subprocess.CalledProcessError:
                return None
        return None
    
    def write_clipboard(self, text: str):
        """Write text to clipboard."""
        if self._tools.get("wl-copy"):
            try:
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode())
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise DesktopBackendError(f"Failed to write clipboard: {e}")
        else:
            raise DesktopBackendError("No clipboard tool available")
    
    def get_selected_text(self) -> Optional[str]:
        """Get selected text using clipboard copy strategy."""
        if not self._tools.get("wl-copy") and not self._tools.get("wl-paste"):
            return None
        
        original = self.read_clipboard()
        
        try:
            if self._tools.get("ydotool"):
                subprocess.run(["ydotool", "key", "ctrl+c"], check=True, timeout=1)
            else:
                return None
            
            import time
            time.sleep(0.1)
            
            selected = self.read_clipboard()
            return selected
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
        finally:
            if original is not None:
                try:
                    self.write_clipboard(original)
                except DesktopBackendError:
                    pass
    
    def get_active_window(self) -> Dict[str, Any]:
        """Get active window information using qdbus."""
        if not self._tools.get("qdbus"):
            return {}
        
        try:
            # Get active window ID
            window_id = subprocess.check_output(
                ["qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.activeWindow"],
                text=True
            ).strip()
            
            # Get window properties
            title = subprocess.check_output(
                ["qdbus", "org.kde.KWin", window_id, "org.kde.kwin.EffectsInterface.title"],
                text=True
            ).strip()
            
            return {
                "id": window_id,
                "name": title
            }
        except subprocess.CalledProcessError:
            return {}
    
    def screenshot(self) -> Optional[bytes]:
        """Take a screenshot using spectacle."""
        if not self._tools.get("spectacle"):
            return None
        
        try:
            return subprocess.check_output(["spectacle", "-b", "-o", "-"])
        except subprocess.CalledProcessError:
            return None
    
    def show_overlay(self, message: str):
        """Show an overlay message."""
        self.notify("GhostType", message)
    
    def notify(self, title: str, message: str):
        """Show a notification."""
        if self._tools.get("notify-send"):
            try:
                subprocess.run(["notify-send", title, message], check=True)
            except subprocess.CalledProcessError:
                print(f"[{title}] {message}")
        else:
            print(f"[{title}] {message}")


def find_kde_tools() -> Dict[str, bool]:
    """Find available KDE tools."""
    tools = [
        "ydotool", "wl-copy", "wl-paste",
        "spectacle", "qdbus", "notify-send"
    ]
    return {tool: bool(shutil.which(tool)) for tool in tools}
