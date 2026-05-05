from typing import Dict, Any, List, Optional
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import PolicyDenied


class PolicyEngine:
    """Main policy engine that coordinates all policy checks."""
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._mode = config.app.mode if hasattr(config, "app") else "fast"
    
    def check(self, text: str) -> Dict[str, Any]:
        """Check policy for text input."""
        result = {
            "mode": self._mode,
            "remote_allowed": True,
            "screenshot_allowed": True,
            "clipboard_allowed": True,
            "selected_text_allowed": True,
            "history_allowed": True,
            "sensitive_app_detected": False,
            "dangerous_command_detected": False,
        }
        
        # Check privacy mode
        if self._mode == "private":
            result["remote_allowed"] = False
            result["screenshot_allowed"] = False
            result["clipboard_allowed"] = False
            result["selected_text_allowed"] = False
            result["history_allowed"] = False
        elif self._mode == "paranoid":
            result["remote_allowed"] = False
            result["screenshot_allowed"] = False
            result["clipboard_allowed"] = False
            result["selected_text_allowed"] = False
            result["history_allowed"] = False
            result["sensitive_app_detected"] = True  # Always assume sensitive
        
        # Check sensitive apps
        from .sensitive_apps import SensitiveApps
        sensitive = SensitiveApps(self.config)
        if sensitive.is_sensitive(text):
            result["sensitive_app_detected"] = True
            if self._mode in ["private", "paranoid"]:
                result["remote_allowed"] = False
                result["screenshot_allowed"] = False
                result["clipboard_allowed"] = False
        
        # Check for dangerous commands
        from .command_safety import CommandSafety
        safety = CommandSafety(self.config)
        if safety.is_dangerous(text):
            result["dangerous_command_detected"] = True
        
        return result
    
    def check_remote(self) -> bool:
        """Check if remote operations are allowed."""
        if self._mode in ["private", "paranoid"]:
            return False
        return True
    
    def check_screenshot(self) -> bool:
        """Check if screenshot is allowed."""
        if self._mode == "paranoid":
            return False
        return True
    
    def check_clipboard(self) -> bool:
        """Check if clipboard access is allowed."""
        if self._mode == "paranoid":
            return False
        return True
    
    def check_history(self) -> bool:
        """Check if history is allowed."""
        if self._mode == "paranoid":
            return False
        return True
