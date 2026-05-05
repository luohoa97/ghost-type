import re
from typing import Dict, Any, List
from ghosttype.core.config import GhostTypeConfig


class CommandSafety:
    """Manages command safety checks."""
    
    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        (r"\brm\s+-rf\b", "rm -rf"),
        (r"\bsudo\b", "sudo"),
        (r"\bdd\b", "dd"),
        (r"\bmkfs\b", "mkfs"),
        (r"\bchmod\s+-R\b", "chmod -R"),
        (r"\bchown\s+-R\b", "chown -R"),
        (r"\bcurl\s+.*\|\s*sh\b", "curl | sh"),
        (r"\bwget\s+.*\|\s*sh\b", "wget | sh"),
        (r"\bdocker\s+system\s+prune\b", "docker system prune"),
        (r"\bgit\s+reset\s+--hard\b", "git reset --hard"),
    ]
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._dangerous_patterns = self.DANGEROUS_PATTERNS.copy()
        
        # Load from config if available
        if hasattr(config, "safety") and hasattr(config.safety, "dangerous_patterns"):
            self._dangerous_patterns = config.safety.dangerous_patterns
    
    def is_dangerous(self, text: str) -> bool:
        """Check if text contains dangerous commands."""
        for pattern, _ in self._dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def get_dangerous_commands(self, text: str) -> List[str]:
        """Get list of dangerous commands detected in text."""
        dangerous = []
        for pattern, name in self._dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                dangerous.append(name)
        return dangerous
    
    def is_safe_to_execute(self, text: str) -> bool:
        """Check if command is safe to execute."""
        if self.is_dangerous(text):
            return False
        return True
