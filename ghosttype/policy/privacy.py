from typing import Dict, Any
from ghosttype.core.config import GhostTypeConfig


class PrivacyPolicy:
    """Privacy policy configuration."""
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._mode = config.app.mode if hasattr(config, "app") else "fast"
    
    @property
    def mode(self) -> str:
        """Get current privacy mode."""
        return self._mode
    
    def is_fast_mode(self) -> bool:
        """Check if fast mode is enabled."""
        return self._mode == "fast"
    
    def is_zdr_mode(self) -> bool:
        """Check if zero-data-removal mode is enabled."""
        return self._mode == "zdr"
    
    def is_private_mode(self) -> bool:
        """Check if private mode is enabled."""
        return self._mode == "private"
    
    def is_paranoid_mode(self) -> bool:
        """Check if paranoid mode is enabled."""
        return self._mode == "paranoid"
    
    def should_store_history(self) -> bool:
        """Check if history should be stored."""
        if self._mode == "paranoid":
            return False
        return True
    
    def should_store_screenshots(self) -> bool:
        """Check if screenshots should be stored."""
        if self._mode == "paranoid":
            return False
        return False  # Never store screenshots by default
    
    def should_store_audio(self) -> bool:
        """Check if audio should be stored."""
        if self._mode == "paranoid":
            return False
        return False  # Never store audio by default
    
    def should_upload_remote(self) -> bool:
        """Check if data should be uploaded to remote services."""
        if self._mode in ["private", "paranoid"]:
            return False
        return True
