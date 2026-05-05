"""Streaming router for GhostType."""
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
import asyncio

from ghosttype.ramblerouter.router import Router, RouterOutput, Action, Route


@dataclass
class StreamingDelta:
    """Delta for streaming updates."""
    text: str = ""
    actions: List[Action] = None
    is_complete: bool = False
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []


class StreamingRouter:
    """Router with streaming support."""
    
    def __init__(self, router: Router, config: Optional[Dict[str, Any]] = None):
        self.router = router
        self.config = config or {}
        
        self._stable_delay_ms = self.config.get("stable_delay_ms", 500)
        self._min_stable_words = self.config.get("min_stable_words", 3)
        self._route_partial_deltas = self.config.get("route_partial_deltas", False)
        self._final_correction_pass = self.config.get("final_correction_pass", True)
    
    async def route_stream(
        self,
        text_stream: AsyncIterator[str]
    ) -> AsyncIterator[StreamingDelta]:
        """Route text as it streams in."""
        pending_text = ""
        stable_prefix = ""
        last_route: Optional[RouterOutput] = None
        
        async for chunk in text_stream:
            pending_text += chunk
            
            # Check for stable prefix
            if len(pending_text.split()) >= self._min_stable_words:
                # Split into stable and pending
                words = pending_text.split()
                stable_prefix = " ".join(words[:-1])
                pending_text = words[-1]
                
                # Route stable prefix
                if self._route_partial_deltas:
                    route = self.router.route(stable_prefix)
                    
                    if route != last_route:
                        yield StreamingDelta(
                            text=stable_prefix,
                            actions=route.actions,
                            is_complete=False,
                        )
                        last_route = route
            
            # Small delay to allow for more stable input
            await asyncio.sleep(self._stable_delay_ms / 1000)
        
        # Route final text
        final_text = stable_prefix + " " + pending_text if stable_prefix else pending_text
        final_route = self.router.route(final_text)
        
        yield StreamingDelta(
            text=final_text,
            actions=final_route.actions,
            is_complete=True,
        )
    
    async def route_with_correction(
        self,
        text: str,
        partial_deltas: List[StreamingDelta]
    ) -> RouterOutput:
        """Route text with final correction pass."""
        # Combine all deltas
        full_text = " ".join(d.text for d in partial_deltas if d.text)
        
        # Route final text
        return self.router.route(full_text)
    
    def is_stable(self, text: str) -> bool:
        """Check if text is stable enough for routing."""
        # Simple stability check
        if len(text.split()) < self._min_stable_words:
            return False
        
        # Check for trailing punctuation
        if text and text[-1] in ".!?":
            return True
        
        return False
    
    def get_pending_text(self, text: str) -> str:
        """Get pending (unstable) text."""
        words = text.split()
        if len(words) <= self._min_stable_words:
            return text
        
        return " ".join(words[-(len(words) - self._min_stable_words):])
    
    def diagnostics(self) -> Dict[str, Any]:
        """Get streaming router diagnostics."""
        return {
            "stable_delay_ms": self._stable_delay_ms,
            "min_stable_words": self._min_stable_words,
            "route_partial_deltas": self._route_partial_deltas,
            "final_correction_pass": self._final_correction_pass,
        }
