import os
import subprocess
from typing import List, Optional, Dict, Any
from .base import DesktopBackend, Capability
from ghosttype.core.errors import DesktopBackendError


class PortalBackend(DesktopBackend):
    """Desktop backend using Flatpak portals for safe operations."""
    
    def __init__(self):
        self._detected = False
        self._portals = {}
    
    def detect(self) -> bool:
        """Detect available portals."""
        # Check if we're in a Flatpak environment
        if os.path.exists("/.flatpak-info"):
            self._detected = True
            self._portals = self._check_portals()
            return True
        
        return False
    
    def get_name(self) -> str:
        return "Portal"
    
    def capabilities(self) -> List[Capability]:
        caps = []
        
        if self._portals.get("screenshot"):
            caps.append(Capability.SCREENSHOT)
        
        if self._portals.get("open_uri"):
            caps.append(Capability.NOTIFICATIONS)
        
        return caps
    
    def score(self) -> int:
        """Score portal backend."""
        if not self._detected:
            return 0
        
        score = 30  # Lower score as portals are limited
        
        if self._portals.get("screenshot"):
            score += 20
        
        return min(score, 100)
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "flatpak": os.path.exists("/.flatpak-info"),
            "portals": self._portals
        }
    
    def _check_portals(self) -> Dict[str, bool]:
        """Check available portals."""
        portals = {}
        
        # Check screenshot portal
        try:
            result = subprocess.run(
                ["flatpak", "info", "org.freedesktop.portal.Screenshot"],
                capture_output=True,
                text=True
            )
            portals["screenshot"] = result.returncode == 0
        except:
            portals["screenshot"] = False
        
        # Check notification portal
        try:
            result = subprocess.run(
                ["flatpak", "info", "org.freedesktop.portal.Notification"],
                capture_output=True,
                text=True
            )
            portals["open_uri"] = result.returncode == 0
        except:
            portals["open_uri"] = False
        
        return portals
    
    def paste_text(self, text: str):
        """Paste text - portals don't support this directly."""
        raise DesktopBackendError(
            "Portal backend doesn't support paste_text. "
            "Use a different backend for input operations."
        )
    
    def type_text(self, text: str):
        """Type text - portals don't support this directly."""
        raise DesktopBackendError(
            "Portal backend doesn't support type_text. "
            "Use a different backend for input operations."
        )
    
    def press_key(self, key: str):
        """Press key - portals don't support this directly."""
        raise DesktopBackendError(
            "Portal backend doesn't support press_key. "
            "Use a different backend for input operations."
        )
    
    def read_clipboard(self) -> Optional[str]:
        """Read clipboard - portals don't support this directly."""
        raise DesktopBackendError(
            "Portal backend doesn't support read_clipboard. "
            "Use a different backend for clipboard operations."
        )
    
    def write_clipboard(self, text: str):
        """Write clipboard - portals don't support this directly."""
        raise DesktopBackendError(
            "Portal backend doesn't support write_clipboard. "
            "Use a different backend for clipboard operations."
        )
    
    def get_selected_text(self) -> Optional[str]:
        """Get selected text - portals don't support this directly."""
        raise DesktopBackendError(
            "Portal backend doesn't support get_selected_text. "
            "Use a different backend for text selection."
        )
    
    def get_active_window(self) -> Dict[str, Any]:
        """Get active window - portals don't support this directly."""
        return {}
    
    def screenshot(self) -> Optional[bytes]:
        """Take a screenshot using portal."""
        if not self._portals.get("screenshot"):
            return None
        
        try:
            # Use grim as fallback when portal not available
            import shutil
            if shutil.which("grim"):
                return subprocess.check_output(["grim", "-"])
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def show_overlay(self, message: str):
        """Show overlay via notification portal."""
        self.notify("GhostType", message)
    
    def notify(self, title: str, message: str):
        """Show a notification."""
        if self._portals.get("open_uri"):
            try:
                # Use notify-send as fallback
                import shutil
                if shutil.which("notify-send"):
                    subprocess.run(["notify-send", title, message], check=True)
                    return
            except subprocess.CalledProcessError:
                pass
        
        print(f"[{title}] {message}")
