import os
import time
from typing import Dict, Any, Optional
from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import ContextError


class ContextManager:
    """Manages all context providers."""
    
    def __init__(self, config: GhostTypeConfig):
        self.config = config
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        self._max_cache_age = 300  # 5 minutes
    
    def get(self, provider_id: str) -> Optional[str]:
        """Get context from a specific provider."""
        # Check cache first
        if provider_id in self._cache:
            if time.time() - self._cache_ttl.get(provider_id, 0) < self._max_cache_age:
                return self._cache[provider_id]
        
        # Import and use provider
        from .clipboard import ClipboardContextProvider
        from .selected_text import SelectedTextContextProvider
        from .active_window import ActiveWindowContextProvider
        from .last_output import LastOutputContextProvider
        from .screenshot_ocr import ScreenshotOCRContextProvider
        from .vocabulary import VocabularyContextProvider
        
        providers = {
            "clipboard": ClipboardContextProvider,
            "selected-text": SelectedTextContextProvider,
            "active-window": ActiveWindowContextProvider,
            "last-output": LastOutputContextProvider,
            "screenshot-ocr": ScreenshotOCRContextProvider,
            "vocabulary": VocabularyContextProvider,
        }
        
        if provider_id not in providers:
            raise ContextError(f"Unknown context provider: {provider_id}")
        
        provider = providers[provider_id](self.config)
        
        if not provider.is_available():
            raise ContextError(f"Provider {provider_id} is not available")
        
        content = provider.get()
        self._cache[provider_id] = content
        self._cache_ttl[provider_id] = time.time()
        
        return content
    
    def collect_all(self) -> Dict[str, str]:
        """Collect all available context."""
        context = {}
        
        for provider_id in ["clipboard", "selected-text", "active-window", "last-output"]:
            try:
                content = self.get(provider_id)
                if content:
                    context[provider_id] = content
            except Exception:
                pass
        
        return context
    
    def clear(self):
        """Clear context cache."""
        self._cache.clear()
        self._cache_ttl.clear()
