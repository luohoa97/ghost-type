import re
from typing import Dict, Any, List
from ghosttype.core.config import GhostTypeConfig


class SensitiveApps:
    """Manages sensitive application detection."""
    
    # Default sensitive applications
    DEFAULT_SENSITIVE_APPS = [
        "keepassxc",
        "bitwarden",
        "1password",
        "gnome-secrets",
        "seahorse",
        "pinentry",
        "ssh-askpass",
    ]
    
    # Default sensitive window patterns
    DEFAULT_SENSITIVE_PATTERNS = [
        r".*password.*",
        r".*keychain.*",
        r".*credential.*",
        r".*secret.*",
        r".*token.*",
        r".*bank.*",
        r".*payment.*",
    ]
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._sensitive_apps = self.DEFAULT_SENSITIVE_APPS.copy()
        self._sensitive_patterns = self.DEFAULT_SENSITIVE_PATTERNS.copy()
        
        # Load from config if available
        if hasattr(config, "privacy") and hasattr(config.privacy, "sensitive_apps"):
            self._sensitive_apps = config.privacy.sensitive_apps
        
        if hasattr(config, "privacy") and hasattr(config.privacy, "sensitive_window_patterns"):
            self._sensitive_patterns = config.privacy.sensitive_window_patterns
    
    def is_sensitive(self, text: str) -> bool:
        """Check if text contains sensitive app names."""
        text_lower = text.lower()
        for app in self._sensitive_apps:
            if app in text_lower:
                return True
        return False
    
    def is_window_sensitive(self, window_name: str) -> bool:
        """Check if window name matches sensitive patterns."""
        for pattern in self._sensitive_patterns:
            if re.search(pattern, window_name, re.IGNORECASE):
                return True
        return False
    
    def get_sensitive_apps(self) -> List[str]:
        """Get list of sensitive apps."""
        return self._sensitive_apps.copy()
    
    def get_sensitive_patterns(self) -> List[str]:
        """Get list of sensitive patterns."""
        return self._sensitive_patterns.copy()
