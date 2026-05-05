from typing import Dict, Any, Optional, List, AsyncIterator, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import re


@dataclass
class EditEvent:
    type: str
    old_text: str = ""
    new_text: str = ""
    position: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "position": self.position,
        }


class EditEventType(Enum):
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    CORRECT = "correct"
    COMMIT = "commit"


@dataclass
class StablePrefix:
    text: str
    confidence: float = 1.0
    is_final: bool = False
    
    def __str__(self) -> str:
        return self.text


@dataclass 
class StreamingState:
    buffer: str = ""
    stable_prefix: str = ""
    pending_text: str = ""
    is_final: bool = False
    
    def reset(self):
        self.buffer = ""
        self.stable_prefix = ""
        self.pending_text = ""
        self.is_final = False


class StablePrefixDetector:
    def __init__(
        self,
        min_words: int = 3,
        stability_delay_ms: int = 500,
        punctuation_weights: Optional[Dict[str, float]] = None,
    ):
        self.min_words = min_words
        self.stability_delay_ms = stability_delay_ms
        self.punctuation_weights = punctuation_weights or {
            ".": 0.9,
            "!": 0.9,
            "?": 0.9,
            ",": 0.5,
            ";": 0.6,
            ":": 0.6,
        }
        self._state = StreamingState()
        self._last_stable_time: Optional[float] = None
    
    def reset(self):
        self._state = StreamingState()
        self._last_stable_time = None
    
    def detect(self, text: str) -> StablePrefix:
        self._state.buffer = text
        
        words = text.split()
        
        if len(words) < self.min_words:
            self._state.pending_text = text
            self._state.stable_prefix = ""
            return StablePrefix(text="", confidence=0.0)
        
        cutoff = len(words) - 1
        stable = " ".join(words[:cutoff])
        pending = words[-1]
        
        self._state.stable_prefix = stable
        self._state.pending_text = pending
        
        confidence = self._calculate_confidence(stable)
        
        return StablePrefix(
            text=stable,
            confidence=confidence,
            is_final=False,
        )
    
    def force_final(self) -> StablePrefix:
        self._state.is_final = True
        full_text = self._state.stable_prefix + " " + self._state.pending_text
        full_text = full_text.strip()
        
        return StablePrefix(
            text=full_text,
            confidence=1.0,
            is_final=True,
        )
    
    def _calculate_confidence(self, text: str) -> float:
        if not text:
            return 0.0
        
        confidence = 0.5
        
        last_char = text[-1] if text else ""
        if last_char in self.punctuation_weights:
            confidence = max(confidence, self.punctuation_weights[last_char])
        
        words = text.split()
        if len(words) >= self.min_words:
            confidence = max(confidence, 0.7)
        
        word_count_bonus = min(len(words) / 20, 0.2)
        confidence += word_count_bonus
        
        return min(confidence, 1.0)
    
    def get_pending(self) -> str:
        return self._state.pending_text
    
    def get_stable(self) -> str:
        return self._state.stable_prefix


class AudioChunkStream:
    def __init__(
        self,
        chunk_size_ms: int = 100,
        vad_enabled: bool = True,
    ):
        self.chunk_size_ms = chunk_size_ms
        self.vad_enabled = vad_enabled
        self._chunks: List[bytes] = []
        self._is_recording = False
    
    async def stream_chunks(
        self,
        source: AsyncIterator[bytes],
    ) -> AsyncIterator[bytes]:
        async for chunk in source:
            self._chunks.append(chunk)
            yield chunk
    
    def get_all_chunks(self) -> List[bytes]:
        return self._chunks.copy()
    
    def clear(self):
        self._chunks.clear()
    
    def get_audio_duration_ms(self) -> int:
        return len(self._chunks) * self.chunk_size_ms
    
    def is_recording(self) -> bool:
        return self._is_recording
    
    def start_recording(self):
        self._is_recording = True
        self._chunks.clear()
    
    def stop_recording(self):
        self._is_recording = False


class STTPartialStream:
    def __init__(
        self,
        stt_provider,
        interim_results: bool = True,
    ):
        self.stt_provider = stt_provider
        self.interim_results = interim_results
        self._partial_text = ""
        self._final_text = ""
    
    async def process_stream(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[Dict[str, Any]]:
        buffer = b""
        
        async for chunk in audio_stream:
            buffer += chunk
            
            if len(buffer) > 3200:
                try:
                    result = await self.stt_provider.transcribe(
                        buffer,
                        interim=self.interim_results,
                    )
                    
                    yield {
                        "type": "partial" if result.get("interim") else "final",
                        "text": result.get("text", ""),
                        "confidence": result.get("confidence", 1.0),
                    }
                    
                    if not result.get("interim"):
                        self._final_text = result.get("text", "")
                    
                    self._partial_text = result.get("text", "")
                    
                except Exception:
                    pass
                
                buffer = b""
    
    def get_partial_text(self) -> str:
        return self._partial_text
    
    def get_final_text(self) -> str:
        return self._final_text


class EditEventStream:
    def __init__(self):
        self._handlers: List[Callable[[EditEvent], Awaitable[None]]] = []
        self._history: List[EditEvent] = []
        self._pending: Optional[EditEvent] = None
    
    def on_edit(self, handler: Callable[[EditEvent], Awaitable[None]]):
        self._handlers.append(handler)
    
    async def emit(self, event: EditEvent):
        self._history.append(event)
        
        for handler in self._handlers:
            await handler(event)
    
    async def emit_insert(self, text: str, position: int):
        await self.emit(EditEvent(
            type=EditEventType.INSERT.value,
            new_text=text,
            position=position,
        ))
    
    async def emit_delete(self, text: str, position: int):
        await self.emit(EditEvent(
            type=EditEventType.DELETE.value,
            old_text=text,
            position=position,
        ))
    
    async def emit_replace(self, old_text: str, new_text: str, position: int):
        await self.emit(EditEvent(
            type=EditEventType.REPLACE.value,
            old_text=old_text,
            new_text=new_text,
            position=position,
        ))
    
    async def emit_correct(self, old_text: str, new_text: str, position: int):
        await self.emit(EditEvent(
            type=EditEventType.CORRECT.value,
            old_text=old_text,
            new_text=new_text,
            position=position,
        ))
    
    def get_history(self) -> List[EditEvent]:
        return self._history.copy()
    
    def clear_history(self):
        self._history.clear()


class StreamingDeltaMode:
    def __init__(
        self,
        stable_detector: StablePrefixDetector,
        route_callback: Optional[Callable[[str], Any]] = None,
    ):
        self.stable_detector = stable_detector
        self.route_callback = route_callback
        self._pending_overlay_text = ""
        self._last_routed_text = ""
        self._correction_enabled = True
    
    def update(self, text: str) -> Optional[Dict[str, Any]]:
        stable = self.stable_detector.detect(text)
        
        self._pending_overlay_text = stable.text
        
        if stable.text != self._last_routed_text and stable.confidence > 0.5:
            self._last_routed_text = stable.text
            
            result = {
                "stable_text": stable.text,
                "pending_text": self.stable_detector.get_pending(),
                "confidence": stable.confidence,
                "is_final": stable.is_final,
            }
            
            if self.route_callback:
                result["routed"] = self.route_callback(stable.text)
            
            return result
        
        return None
    
    def finalize(self) -> Dict[str, Any]:
        final = self.stable_detector.force_final()
        
        return {
            "final_text": final.text,
            "confidence": final.confidence,
            "is_final": True,
        }
    
    def enable_correction(self, enabled: bool = True):
        self._correction_enabled = enabled
    
    def get_pending_overlay(self) -> str:
        return self._pending_overlay_text


class FinalCorrectionPass:
    def __init__(
        self,
        correction_llm,
        min_confidence_threshold: float = 0.7,
    ):
        self.correction_llm = correction_llm
        self.min_confidence_threshold = min_confidence_threshold
    
    async def correct(
        self,
        text: str,
        confidence: float,
    ) -> str:
        if confidence >= self.min_confidence_threshold:
            return text
        
        if not self.correction_llm or not self.correction_llm.is_available():
            return text
        
        prompt = f"""Review and correct the following transcribed text for accuracy.
Only fix clear transcription errors, do not change the meaning.

Text: "{text}"

Return the corrected text only."""

        try:
            response = self.correction_llm.complete({
                "messages": [{"role": "user", "content": prompt}]
            })
            return response.get("content", text)
        except Exception:
            return text
    
    def set_threshold(self, threshold: float):
        self.min_confidence_threshold = threshold


class PendingOverlay:
    def __init__(
        self,
        text_renderer: Optional[Callable[[str], None]] = None,
    ):
        self._text_renderer = text_renderer
        self._current_text = ""
        self._is_visible = False
    
    def show(self, text: str):
        self._current_text = text
        self._is_visible = True
        
        if self._text_renderer:
            self._text_renderer(text)
    
    def update(self, text: str):
        self._current_text = text
        
        if self._text_renderer:
            self._text_renderer(text)
    
    def hide(self):
        self._is_visible = False
        self._current_text = ""
        
        if self._text_renderer:
            self._text_renderer("")
    
    def get_text(self) -> str:
        return self._current_text
    
    def is_visible(self) -> bool:
        return self._is_visible


class StreamingOrchestrator:
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.config = config or {}
        
        self.stable_detector = StablePrefixDetector(
            min_words=self.config.get("min_stable_words", 3),
            stability_delay_ms=self.config.get("stability_delay_ms", 500),
        )
        
        self.delta_mode = StreamingDeltaMode(
            stable_detector=self.stable_detector,
        )
        
        self.edit_events = EditEventStream()
        self.pending_overlay = PendingOverlay()
        
        self.correction_llm = None
        self.correction_pass = None
        
        self._is_active = False
    
    def set_correction_llm(self, llm):
        self.correction_llm = llm
        self.correction_pass = FinalCorrectionPass(llm)
    
    async def process_text_stream(
        self,
        text_stream: AsyncIterator[str],
    ) -> AsyncIterator[Dict[str, Any]]:
        self._is_active = True
        
        async for text in text_stream:
            delta = self.delta_mode.update(text)
            
            if delta:
                self.pending_overlay.update(delta.get("stable_text", ""))
                
                yield delta
                
                await self._process_edit_events(delta)
        
        if self._is_active:
            final = self.delta_mode.finalize()
            
            if self.correction_pass and final.get("is_final"):
                corrected = await self.correction_pass.correct(
                    final.get("final_text", ""),
                    final.get("confidence", 1.0),
                )
                final["corrected_text"] = corrected
            
            yield final
            
            self.pending_overlay.hide()
        
        self._is_active = False
    
    async def _process_edit_events(self, delta: Dict[str, Any]):
        stable_text = delta.get("stable_text", "")
        
        if stable_text:
            await self.edit_events.emit_insert(
                text=stable_text,
                position=0,
            )
    
    def reset(self):
        self.stable_detector.reset()
        self.delta_mode._last_routed_text = ""
        self.edit_events.clear_history()
        self.pending_overlay.hide()
        self._is_active = False
    
    def is_active(self) -> bool:
        return self._is_active
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "stable_detector": {
                "min_words": self.stable_detector.min_words,
                "stability_delay_ms": self.stable_detector.stability_delay_ms,
            },
            "correction_enabled": self.correction_pass is not None,
            "is_active": self._is_active,
            "pending_text": self.delta_mode.get_pending_overlay(),
        }
