import os
import shutil
import subprocess
from typing import List, Optional, Dict, Any
from .base import DesktopBackend, Capability
from ghosttype.core.errors import DesktopBackendError


class X11Backend(DesktopBackend):
    """Desktop backend for X11 sessions."""
    
    def __init__(self):
        self._detected = False
        self._tools = {}
    
    def detect(self) -> bool:
        """Detect X11 session and available tools."""
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        display = os.environ.get("DISPLAY")
        
        # X11 detection
        if session_type == "x11" or display is not None:
            self._detected = True
            self._tools = find_x11_tools()
            return True
        
        return False
    
    def get_name(self) -> str:
        return "X11"
    
    def capabilities(self) -> List[Capability]:
        caps = []
        
        if self._tools.get("xdotool"):
            caps.extend([
                Capability.TYPE_TEXT,
                Capability.PRESS_KEY,
                Capability.KEY_DOWN_UP
            ])
        
        if self._tools.get("xclip") or self._tools.get("xsel"):
            caps.extend([
                Capability.READ_CLIPBOARD,
                Capability.WRITE_CLIPBOARD
            ])
        
        if self._tools.get("xdotool") or self._tools.get("wmctrl") or self._tools.get("xprop"):
            caps.append(Capability.ACTIVE_WINDOW)
        
        if self._tools.get("maim") or self._tools.get("scrot"):
            caps.append(Capability.SCREENSHOT)
        
        if self._tools.get("notify-send"):
            caps.append(Capability.NOTIFICATIONS)
        
        if self._tools.get("xdotool"):
            caps.append(Capability.OVERLAY)
        
        return caps
    
    def score(self) -> int:
        """Score X11 backend based on available tools."""
        if not self._detected:
            return 0
        
        score = 50  # Base score for X11
        
        # Bonus for key tools
        if self._tools.get("xdotool"):
            score += 30
        if self._tools.get("xclip") or self._tools.get("xsel"):
            score += 20
        if self._tools.get("maim") or self._tools.get("scrot"):
            score += 15
        if self._tools.get("notify-send"):
            score += 10
        
        return min(score, 100)
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "session_type": "x11",
            "display": os.environ.get("DISPLAY"),
            "tools": self._tools
        }
    
    def paste_text(self, text: str):
        """Paste text using clipboard."""
        self.write_clipboard(text)
        
        # Simulate Ctrl+V
        if self._tools.get("xdotool"):
            try:
                subprocess.run(["xdotool", "key", "ctrl+v"], check=True)
            except subprocess.CalledProcessError as e:
                raise DesktopBackendError(f"Failed to paste: {e}")
        else:
            raise DesktopBackendError("No paste tool available (xdotool)")
    
    def type_text(self, text: str):
        """Type text directly."""
        if not self._tools.get("xdotool"):
            raise DesktopBackendError("xdotool not available")
        
        try:
            # Type text with proper escaping
            escaped_text = text.replace("\\", "\\\\").replace(" ", "\\ ")
            subprocess.run(["xdotool", "type", escaped_text], check=True)
        except subprocess.CalledProcessError as e:
            raise DesktopBackendError(f"Failed to type text: {e}")
    
    def press_key(self, key: str):
        """Press a key."""
        if not self._tools.get("xdotool"):
            raise DesktopBackendError("xdotool not available")
        
        try:
            subprocess.run(["xdotool", "key", key], check=True)
        except subprocess.CalledProcessError as e:
            raise DesktopBackendError(f"Failed to press key: {e}")
    
    def read_clipboard(self) -> Optional[str]:
        """Read clipboard content."""
        if self._tools.get("xclip"):
            try:
                return subprocess.check_output(["xclip", "-selection", "clipboard", "-o"], text=True)
            except subprocess.CalledProcessError:
                return None
        elif self._tools.get("xsel"):
            try:
                return subprocess.check_output(["xsel", "--clipboard", "--output"], text=True)
            except subprocess.CalledProcessError:
                return None
        return None
    
    def write_clipboard(self, text: str):
        """Write text to clipboard."""
        if self._tools.get("xclip"):
            try:
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode())
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise DesktopBackendError(f"Failed to write clipboard: {e}")
        elif self._tools.get("xsel"):
            try:
                p = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode())
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise DesktopBackendError(f"Failed to write clipboard: {e}")
        else:
            raise DesktopBackendError("No clipboard tool available")
    
    def get_selected_text(self) -> Optional[str]:
        """Get selected text using clipboard copy strategy."""
        if not self._tools.get("xclip") and not self._tools.get("xsel"):
            return None
        
        # Save current clipboard
        original = self.read_clipboard()
        
        try:
            # Press Ctrl+C
            subprocess.run(["xdotool", "key", "ctrl+c"], check=True, timeout=1)
            
            # Small delay for clipboard to update
            import time
            time.sleep(0.1)
            
            # Read clipboard
            selected = self.read_clipboard()
            return selected
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
        finally:
            # Restore original clipboard
            if original is not None:
                try:
                    self.write_clipboard(original)
                except DesktopBackendError:
                    pass
    
    def get_active_window(self) -> Dict[str, Any]:
        """Get active window information."""
        if not self._tools.get("xdotool"):
            return {}
        
        try:
            # Get window ID
            window_id = subprocess.check_output(["xdotool", "getactivewindow"], text=True).strip()
            
            # Get window name
            name = subprocess.check_output(["xdotool", "getwindowname", window_id], text=True).strip()
            
            # Get window class
            window_class = subprocess.check_output(
                ["xdotool", "getwindowclass", window_id], 
                text=True
            ).strip().split()
            
            return {
                "id": window_id,
                "name": name,
                "class": window_class[1] if len(window_class) > 1 else window_class[0]
            }
        except subprocess.CalledProcessError:
            return {}
    
    def screenshot(self) -> Optional[bytes]:
        """Take a screenshot."""
        if self._tools.get("maim"):
            try:
                return subprocess.check_output(["maim", "-s"])
            except subprocess.CalledProcessError:
                return None
        elif self._tools.get("scrot"):
            try:
                return subprocess.check_output(["scrot", "-s", "-"])
            except subprocess.CalledProcessError:
                return None
        return None
    
    def show_overlay(self, message: str):
        """Show an overlay message."""
        if self._tools.get("notify-send"):
            self.notify("GhostType", message)
        else:
            # Fallback to printing
            print(f"[GhostType Overlay] {message}")
    
    def notify(self, title: str, message: str):
        """Show a notification."""
        if self._tools.get("notify-send"):
            try:
                subprocess.run(["notify-send", title, message], check=True)
            except subprocess.CalledProcessError:
                print(f"[{title}] {message}")
        else:
            print(f"[{title}] {message}")


def find_x11_tools() -> Dict[str, bool]:
    """Find available X11 tools."""
    tools = [
        "xdotool", "xclip", "xsel", "wmctrl", "xprop",
        "maim", "scrot", "notify-send"
    ]
    return {tool: bool(shutil.which(tool)) for tool in tools}
