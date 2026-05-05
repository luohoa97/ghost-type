import os
import time
import base64
from typing import Optional
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import ContextError
from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry


class ScreenshotOCRContextProvider:
    """Provides OCR result from screenshot as context."""
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._backend = DesktopRegistry.detect_best_backend()
        self._cache_path = None
        self._cache_ttl = 300  # 5 minutes
    
    def is_available(self) -> bool:
        """Check if OCR provider is available."""
        # Check screenshot capability
        caps = self._backend.capabilities()
        has_screenshot = any(c.value == "screenshot" for c in caps)
        
        # Check tesseract
        import shutil
        has_tesseract = bool(shutil.which("tesseract"))
        
        return has_screenshot and has_tesseract
    
    def get(self) -> Optional[str]:
        """Get OCR result from screenshot."""
        if not self.is_available():
            raise ContextError("OCR provider not available")
        
        # Take screenshot
        img = self._backend.screenshot()
        if not img:
            return None
        
        # Save to temp file for tesseract
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(img)
            img_path = f.name
        
        try:
            # Run tesseract
            import subprocess
            result = subprocess.run(
                ["tesseract", img_path, "stdout"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        finally:
            os.unlink(img_path)
    
    def get_from_cache(self) -> Optional[str]:
        """Get OCR result from cache."""
        if self._cache_path and os.path.exists(self._cache_path):
            with open(self._cache_path, "r") as f:
                return f.read()
        return None
    
    def clear_cache(self):
        """Clear OCR cache."""
        if self._cache_path and os.path.exists(self._cache_path):
            os.unlink(self._cache_path)
            self._cache_path = None
    
    def diagnostics(self) -> dict:
        """Get diagnostics."""
        return {
            "available": self.is_available(),
            "backend": self._backend.get_name(),
            "capabilities": [c.value for c in self._backend.capabilities()],
        }
