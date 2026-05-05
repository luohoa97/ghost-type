import os
import shutil
import subprocess
from typing import List, Optional, Dict, Any
from .base import DesktopBackend, Capability
from ghosttype.core.errors import DesktopBackendError


class WlrootsBackend(DesktopBackend):
    """Desktop backend for wlroots-based sessions (Sway, Hyprland, etc.)."""
    
    def __init__(self):
        self._detected = False
        self._wm = None
        self._tools = {}
    
    def detect(self) -> bool:
        """Detect wlroots-based session."""
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        
        # Check for known wm environment variables
        if os.environ.get("SWAYSOCK"):
            self._wm = "sway"
        elif os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            self._wm = "hyprland"
        else:
            return False
        
        if session_type == "wayland":
            self._detected = True
            self._tools = find_wlroots_tools()
            return True
        
        return False
    
    def get_name(self) -> str:
        if self._wm:
            return f"Wlroots_{self._wm.capitalize()}"
        return "Wlroots"
    
    def capabilities(self) -> List[Capability]:
        caps = []
        
        if self._tools.get("wtype"):
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
        
        if self._tools.get("grim") or self._tools.get("slurp"):
            caps.append(Capability.SCREENSHOT)
        
        if self._wm == "sway" and self._tools.get("swaymsg"):
            caps.append(Capability.ACTIVE_WINDOW)
        
        if self._wm == "hyprland" and self._tools.get("hyprctl"):
            caps.append(Capability.ACTIVE_WINDOW)
        
        if self._tools.get("notify-send"):
            caps.append(Capability.NOTIFICATIONS)
        
        if self._tools.get("wtype"):
            caps.append(Capability.OVERLAY)
        
        return caps
    
    def score(self) -> int:
        """Score wlroots backend."""
        if not self._detected:
            return 0
        
        score = 65  # Base score for wlroots
        
        # Bonus for available tools
        if self._tools.get("wtype"):
            score += 25
        if self._tools.get("wl-copy") or self._tools.get("wl-paste"):
            score += 15
        if self._tools.get("grim") or self._tools.get("slurp"):
            score += 10
        if self._tools.get("notify-send"):
            score += 10
        
        return min(score, 100)
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "session_type": "wayland",
            "window_manager": self._wm,
            "display": os.environ.get("WAYLAND_DISPLAY"),
            "tools": self._tools
        }
    
    def paste_text(self, text: str):
        """Paste text using clipboard."""
        self.write_clipboard(text)
        
        if self._tools.get("wtype"):
            try:
                subprocess.run(["wtype", "-k", "ctrl+v"], check=True)
            except subprocess.CalledProcessError as e:
                raise DesktopBackendError(f"Failed to paste: {e}")
        else:
            self.notify("GhostType", "Text copied to clipboard. Please paste manually (Ctrl+V).")
    
    def type_text(self, text: str):
        """Type text using wtype."""
        if not self._tools.get("wtype"):
            raise DesktopBackendError("wtype not available")
        
        try:
            # wtype handles text directly
            subprocess.run(["wtype", text], check=True)
        except subprocess.CalledProcessError as e:
            raise DesktopBackendError(f"Failed to type text: {e}")
    
    def press_key(self, key: str):
        """Press a key using wtype."""
        if not self._tools.get("wtype"):
            raise DesktopBackendError("wtype not available")
        
        try:
            subprocess.run(["wtype", "-k", key], check=True)
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
            if self._tools.get("wtype"):
                subprocess.run(["wtype", "-k", "ctrl+c"], check=True, timeout=1)
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
        """Get active window information."""
        if self._wm == "sway" and self._tools.get("swaymsg"):
            try:
                # Get focused window
                result = subprocess.check_output(
                    ["swaymsg", "-t", "get_tree"],
                    text=True
                )
                
                import json
                tree = json.loads(result)
                
                # Find focused node
                focused = self._find_focused_node(tree)
                if focused:
                    return {
                        "id": focused.get("id"),
                        "name": focused.get("name", "Unknown"),
                        "app_id": focused.get("app_id")
                    }
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                pass
        
        elif self._wm == "hyprland" and self._tools.get("hyprctl"):
            try:
                # Get active window
                result = subprocess.check_output(
                    ["hyprctl", "activewindow", "-j"],
                    text=True
                )
                
                import json
                window = json.loads(result)
                return {
                    "id": window.get("address", ""),
                    "name": window.get("title", "Unknown"),
                    "app_id": window.get("class", "")
                }
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                pass
        
        return {}
    
    def _find_focused_node(self, node: Dict) -> Optional[Dict]:
        """Recursively find focused node in sway tree."""
        if node.get("focused"):
            return node
        for child in node.get("nodes", []):
            result = self._find_focused_node(child)
            if result:
                return result
        return None
    
    def screenshot(self) -> Optional[bytes]:
        """Take a screenshot using grim."""
        if not self._tools.get("grim"):
            return None
        
        try:
            return subprocess.check_output(["grim", "-"])
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


def find_wlroots_tools() -> Dict[str, bool]:
    """Find available wlroots tools."""
    tools = [
        "wtype", "wl-copy", "wl-paste",
        "grim", "slurp", "swaymsg", "hyprctl", "notify-send"
    ]
    return {tool: bool(shutil.which(tool)) for tool in tools}
