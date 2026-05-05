import pytest
import asyncio
from ghosttype.ramblerouter.streaming_architecture import (
    StablePrefixDetector,
    StablePrefix,
    EditEvent,
    EditEventType,
    EditEventStream,
    PendingOverlay,
    StreamingState,
)


class TestStablePrefixDetector:
    def test_detector_initialization(self):
        detector = StablePrefixDetector(min_words=3)
        assert detector.min_words == 3
        assert detector.stability_delay_ms == 500
    
    def test_detector_with_short_text(self):
        detector = StablePrefixDetector(min_words=3)
        result = detector.detect("Hello")
        
        assert isinstance(result, StablePrefix)
        assert result.text == ""
        assert result.confidence == 0.0
    
    def test_detector_with_threshold_text(self):
        detector = StablePrefixDetector(min_words=3)
        result = detector.detect("Hello world testing")
        
        assert result.text == "Hello world"
        assert result.confidence > 0.5
    
    def test_detector_with_punctuation(self):
        detector = StablePrefixDetector(min_words=2)
        result = detector.detect("Hello world.")
        
        assert result.text == "Hello"
        assert result.confidence > 0.7
    
    def test_detector_force_final(self):
        detector = StablePrefixDetector(min_words=3)
        detector.detect("Hello world testing")
        result = detector.force_final()
        
        assert result.is_final is True
        assert result.confidence == 1.0
        assert "Hello" in result.text
    
    def test_detector_reset(self):
        detector = StablePrefixDetector(min_words=3)
        detector.detect("Hello world testing")
        detector.reset()
        
        assert detector._state.buffer == ""
        assert detector._state.stable_prefix == ""
    
    def test_detector_get_pending(self):
        detector = StablePrefixDetector(min_words=3)
        detector.detect("Hello world testing")
        
        assert detector.get_pending() == "testing"
    
    def test_detector_get_stable(self):
        detector = StablePrefixDetector(min_words=3)
        detector.detect("Hello world testing")
        
        assert detector.get_stable() == "Hello world"


class TestEditEvent:
    def test_edit_event_creation(self):
        event = EditEvent(
            type=EditEventType.INSERT.value,
            new_text="Hello",
            position=0,
        )
        
        assert event.type == "insert"
        assert event.new_text == "Hello"
        assert event.position == 0
    
    def test_edit_event_to_dict(self):
        event = EditEvent(
            type=EditEventType.DELETE.value,
            old_text="Hello",
            position=0,
        )
        
        result = event.to_dict()
        
        assert result["type"] == "delete"
        assert result["old_text"] == "Hello"
        assert result["position"] == 0


class TestEditEventStream:
    def test_edit_event_stream_initialization(self):
        stream = EditEventStream()
        assert len(stream._handlers) == 0
        assert len(stream._history) == 0
    
    @pytest.mark.asyncio
    async def test_edit_event_emit(self):
        stream = EditEventStream()
        received = []
        
        async def handler(event):
            received.append(event)
        
        stream.on_edit(handler)
        await stream.emit_insert("Hello", 0)
        
        assert len(received) == 1
        assert received[0].new_text == "Hello"
    
    @pytest.mark.asyncio
    async def test_edit_event_emit_insert(self):
        stream = EditEventStream()
        await stream.emit_insert("test", 5)
        
        history = stream.get_history()
        assert len(history) == 1
        assert history[0].type == "insert"
        assert history[0].new_text == "test"
    
    @pytest.mark.asyncio
    async def test_edit_event_emit_delete(self):
        stream = EditEventStream()
        await stream.emit_delete("test", 5)
        
        history = stream.get_history()
        assert len(history) == 1
        assert history[0].type == "delete"
    
    @pytest.mark.asyncio
    async def test_edit_event_emit_replace(self):
        stream = EditEventStream()
        await stream.emit_replace("old", "new", 0)
        
        history = stream.get_history()
        assert len(history) == 1
        assert history[0].type == "replace"
    
    def test_edit_event_clear_history(self):
        stream = EditEventStream()
        stream._history.append(EditEvent(type="test"))
        stream.clear_history()
        
        assert len(stream._history) == 0


class TestPendingOverlay:
    def test_pending_overlay_initialization(self):
        overlay = PendingOverlay()
        assert overlay._current_text == ""
        assert overlay._is_visible is False
    
    def test_pending_overlay_show(self):
        overlay = PendingOverlay()
        overlay.show("Hello")
        
        assert overlay._current_text == "Hello"
        assert overlay._is_visible is True
    
    def test_pending_overlay_update(self):
        overlay = PendingOverlay()
        overlay.show("Hello")
        overlay.update("World")
        
        assert overlay._current_text == "World"
        assert overlay._is_visible is True
    
    def test_pending_overlay_hide(self):
        overlay = PendingOverlay()
        overlay.show("Hello")
        overlay.hide()
        
        assert overlay._current_text == ""
        assert overlay._is_visible is False
    
    def test_pending_overlay_get_text(self):
        overlay = PendingOverlay()
        overlay.show("Hello")
        
        assert overlay.get_text() == "Hello"
    
    def test_pending_overlay_is_visible(self):
        overlay = PendingOverlay()
        assert overlay.is_visible() is False
        
        overlay.show("Hello")
        assert overlay.is_visible() is True
    
    def test_pending_overlay_with_renderer(self):
        rendered_text = []
        
        def renderer(text):
            rendered_text.append(text)
        
        overlay = PendingOverlay(text_renderer=renderer)
        overlay.show("Hello")
        
        assert rendered_text == ["Hello"]


class TestStreamingState:
    def test_streaming_state_initialization(self):
        state = StreamingState()
        assert state.buffer == ""
        assert state.stable_prefix == ""
        assert state.pending_text == ""
        assert state.is_final is False
    
    def test_streaming_state_reset(self):
        state = StreamingState()
        state.buffer = "test"
        state.stable_prefix = "Hello"
        state.pending_text = "world"
        state.reset()
        
        assert state.buffer == ""
        assert state.stable_prefix == ""
        assert state.pending_text == ""
        assert state.is_final is False
