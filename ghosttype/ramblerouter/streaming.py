from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
import asyncio

from ghosttype.ramblerouter.router import Router, RouterOutput, Action, Route
from .streaming_architecture import (
    StablePrefixDetector,
    StreamingDeltaMode,
    EditEventStream,
    PendingOverlay,
    StreamingOrchestrator,
)


@dataclass
class StreamingDelta:
    """Delta for streaming updates."""
    text: str = ""
    actions: List[Action] = None
    is_complete: bool = False
    confidence: float = 1.0
    pending_text: str = ""
    stable_text: str = ""
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "actions": [a.to_dict() for a in self.actions],
            "is_complete": self.is_complete,
            "confidence": self.confidence,
            "pending_text": self.pending_text,
            "stable_text": self.stable_text,
        }


class StreamingRouter:
    """Router with streaming support."""
    
    def __init__(self, router: Router, config: Optional[Dict[str, Any]] = None):
        self.router = router
        self.config = config or {}
        
        self._stable_delay_ms = self.config.get("stable_delay_ms", 500)
        self._min_stable_words = self.config.get("min_stable_words", 3)
        self._route_partial_deltas = self.config.get("route_partial_deltas", False)
        self._final_correction_pass = self.config.get("final_correction_pass", True)
        
        self._stable_detector = StablePrefixDetector(
            min_words=self._min_stable_words,
            stability_delay_ms=self._stable_delay_ms,
        )
        
        self._orchestrator: Optional[StreamingOrchestrator] = None
    
    def _get_orchestrator(self) -> StreamingOrchestrator:
        if self._orchestrator is None:
            self._orchestrator = StreamingOrchestrator(config=self.config)
            
            if self.router.strong_llm:
                self._orchestrator.set_correction_llm(self.router.strong_llm)
        
        return self._orchestrator
    
    async def route_stream(
        self,
        text_stream: AsyncIterator[str]
    ) -> AsyncIterator[StreamingDelta]:
        orchestrator = self._get_orchestrator()
        
        async for event in orchestrator.process_text_stream(text_stream):
            if event.get("is_final"):
                yield StreamingDelta(
                    text=event.get("final_text", ""),
                    actions=[],
                    is_complete=True,
                    confidence=event.get("confidence", 1.0),
                    corrected_text=event.get("corrected_text"),
                )
            else:
                stable_text = event.get("stable_text", "")
                pending_text = event.get("pending_text", "")
                
                actions = []
                if self._route_partial_deltas and stable_text:
                    route = self.router.route(stable_text)
                    actions = route.actions
                
                yield StreamingDelta(
                    text=stable_text + " " + pending_text,
                    actions=actions,
                    is_complete=False,
                    confidence=event.get("confidence", 0.5),
                    pending_text=pending_text,
                    stable_text=stable_text,
                )
    
    async def route_with_correction(
        self,
        text: str,
        partial_deltas: List[StreamingDelta]
    ) -> RouterOutput:
        """Route text with final correction pass."""
        full_text = " ".join(d.text for d in partial_deltas if d.text)
        
        return self.router.route(full_text)
    
    def is_stable(self, text: str) -> bool:
        """Check if text is stable enough for routing."""
        if len(text.split()) < self._min_stable_words:
            return False
        
        if text and text[-1] in ".!?":
            return True
        
        return False
    
    def get_pending_text(self, text: str) -> str:
        """Get pending (unstable) text."""
        words = text.split()
        if len(words) <= self._min_stable_words:
            return text
        
        return " ".join(words[-(len(words) - self._min_stable_words):])
    
    def get_edit_events(self) -> EditEventStream:
        return self._get_orchestrator().edit_events
    
    def get_pending_overlay(self) -> PendingOverlay:
        return self._get_orchestrator().pending_overlay
    
    def reset(self):
        if self._orchestrator:
            self._orchestrator.reset()
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "stable_delay_ms": self._stable_delay_ms,
            "min_stable_words": self._min_stable_words,
            "route_partial_deltas": self._route_partial_deltas,
            "final_correction_pass": self._final_correction_pass,
            "orchestrator": self._get_orchestrator().diagnostics(),
        }
