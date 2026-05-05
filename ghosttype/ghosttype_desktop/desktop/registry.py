import os
import shutil
from typing import List, Type, Dict, Any, Optional
from .base import DesktopBackend, Capability

class DesktopRegistry:
    """Registry and detector for desktop backends."""
    
    _backends: List[Type[DesktopBackend]] = []
    _detected_backend: Optional[DesktopBackend] = None
    
    @classmethod
    def register_backend(cls, backend_class: Type[DesktopBackend]):
        """Register a desktop backend class."""
        cls._backends.append(backend_class)
    
    @classmethod
    def detect_best_backend(cls) -> DesktopBackend:
        """Detect and return the best available desktop backend."""
        if cls._detected_backend is not None:
            return cls._detected_backend
        
        # Get all detected backends with their scores
        scored_backends = []
        for backend_class in cls._backends:
            backend = backend_class()
            if backend.detect():
                scored_backends.append((backend, backend.score()))
        
        if not scored_backends:
            # Fallback to generic clipboard backend
            from .generic import GenericClipboardBackend
            cls._detected_backend = GenericClipboardBackend()
            return cls._detected_backend
        
        # Sort by score (highest first)
        scored_backends.sort(key=lambda x: x[1], reverse=True)
        cls._detected_backend = scored_backends[0][0]
        return cls._detected_backend
    
    @classmethod
    def get_all_backends(cls) -> List[DesktopBackend]:
        """Get all registered backends."""
        return [backend_class() for backend_class in cls._backends]
    
    @classmethod
    def get_backend_by_name(cls, name: str) -> Optional[DesktopBackend]:
        """Get a backend by its name."""
        for backend_class in cls._backends:
            backend = backend_class()
            if backend.get_name() == name:
                return backend
        return None
    
    @classmethod
    def detect_all(cls) -> List[Dict[str, Any]]:
        """Detect all available backends and their scores."""
        results = []
        for backend_class in cls._backends:
            backend = backend_class()
            detected = backend.detect()
            results.append({
                "name": backend.get_name(),
                "detected": detected,
                "score": backend.score() if detected else 0,
                "capabilities": [c.value for c in backend.capabilities()] if detected else []
            })
        return results
    
    @classmethod
    def get_capabilities(cls) -> List[Capability]:
        """Get capabilities of the best backend."""
        backend = cls.detect_best_backend()
        return backend.capabilities()
    
    @classmethod
    def get_diagnostics(cls) -> Dict[str, Any]:
        """Get diagnostics for all backends."""
        backends = cls.get_all_backends()
        return {
            "best_backend": cls.detect_best_backend().get_name(),
            "backends": [
                {
                    "name": b.get_name(),
                    "score": b.score(),
                    "capabilities": [c.value for c in b.capabilities()],
                    "tools": b.diagnostics()
                }
                for b in backends
            ]
        }


def detect_session_type() -> str:
    """Detect the current session type."""
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session_type:
        return session_type
    
    # Fallback detection
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def detect_desktop_environment() -> str:
    """Detect the current desktop environment."""
    de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if de:
        return de
    
    session = os.environ.get("DESKTOP_SESSION", "").lower()
    if session:
        return session
    
    return "unknown"


def detect_wm() -> str:
    """Detect the window manager for wlroots-based sessions."""
    if os.environ.get("SWAYSOCK"):
        return "sway"
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"
    return "unknown"


def find_tool(name: str) -> Optional[str]:
    """Check if a tool is available in PATH."""
    return shutil.which(name)


def find_tools(names: List[str]) -> Dict[str, bool]:
    """Check if multiple tools are available."""
    return {name: bool(find_tool(name)) for name in names}


# Register backends
from .x11 import X11Backend
from .gnome_wayland import GnomeWaylandBackend
from .gnome_extension import GnomeExtensionBackend
from .kde_wayland import KDEWaylandBackend
from .wlroots import WlrootsBackend
from .portal import PortalBackend
from .generic import GenericClipboardBackend
