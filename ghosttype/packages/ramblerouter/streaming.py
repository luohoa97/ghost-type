from typing import Dict, Any, AsyncIterator, Optional
from ghosttype.core.errors import RouterError


class StreamingRouter:
    """Handles streaming routing for real-time processing."""
    
    def __init__(self):
        self._stable_prefix_detector = StablePrefixDetector()
    
    async def route_stream(self, text_stream: AsyncIterator[str]) -> AsyncIterator[Dict[str, Any]]:
        """Route streaming text to actions."""
        pending_text = ""
        
        async for chunk in text_stream:
            pending_text += chunk
            
            # Check for stable prefix
            stable, delta = self._stable_prefix_detector.detect(pending_text)
            
            if stable:
                # Route the stable part
                actions = self._route_text(stable)
                yield {
                    "type": "actions",
                    "actions": actions,
                    "delta": delta,
                }
                
                # Reset pending text
                pending_text = delta
        
        # Route remaining text
        if pending_text:
            actions = self._route_text(pending_text)
            yield {
                "type": "actions",
                "actions": actions,
                "delta": "",
            }
    
    def _route_text(self, text: str) -> list:
        """Route text to actions."""
        # Use deterministic parser for streaming
        from .router import DeterministicParser
        parser = DeterministicParser()
        return parser.parse(text) or [{"type": "insert_text", "text": text}]


class StablePrefixDetector:
    """Detects stable prefixes in streaming text."""
    
    def __init__(self):
        self._min_stable_words = 3
        self._stable_delay_ms = 500
    
    def detect(self, text: str) -> tuple:
        """Detect stable prefix in text."""
        words = text.split()
        
        if len(words) < self._min_stable_words:
            return "", text
        
        # Consider everything except last word as stable
        stable = " ".join(words[:-1])
        delta = words[-1]
        
        return stable, delta
