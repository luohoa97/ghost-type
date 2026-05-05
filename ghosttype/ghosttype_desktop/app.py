"""GhostType Desktop Application - Main integration point."""
import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from threading import Event, Thread
from dataclasses import dataclass

from core.config import ConfigManager, GhostTypeConfig
from core.errors import STTError, CapabilityUnavailable
from ghosttype_desktop.audio.recorder import AudioRecorder, detect_audio_devices
from ghosttype_desktop.audio.vad import VoiceActivityDetector
from ghosttype_desktop.input.keyd import KeydProvider, KeydEvent
from ghosttype_desktop.input.evdev import EvdevProvider, EvdevEvent
from ghosttype_desktop.output.injector import ActionExecutor
from ghosttype_desktop.desktop.registry import DesktopRegistry
from ramblerouter.router import Router
from ramblerouter.streaming import StreamingRouter
from providers.stt.groq_whisper import GroqWhisperProvider
from ghosttype_desktop.overlay.overlay import OverlayAbstraction, create_overlay


@dataclass
class AppState:
    """Application state."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    RESULT = "result"
    ERROR = "error"


class GhostTypeDesktopApp:
    """Main GhostType desktop application integrating all components."""

    def __init__(self, config: Optional[GhostTypeConfig] = None):
        self.config = config or ConfigManager().config

        self._state = AppState.IDLE
        self._recorder: Optional[AudioRecorder] = None
        self._vad: Optional[VoiceActivityDetector] = None
        self._input_provider = None
        self._router: Optional[Router] = None
        self._streaming_router: Optional[StreamingRouter] = None
        self._executor: Optional[ActionExecutor] = None
        self._overlay: Optional[OverlayAbstraction] = None

        self._recording = False
        self._hold_mode = True
        self._key_pressed = False

        self._event_callback: Optional[Callable] = None
        self._transcript_callback: Optional[Callable[[str], None]] = None

        self._logger = logging.getLogger("ghosttype.app")

        self._initialize()

    def _initialize(self):
        """Initialize all components."""
        self._initialize_audio()
        self._initialize_input()
        self._initialize_router()
        self._initialize_output()
        self._initialize_overlay()

    def _initialize_audio(self):
        """Initialize audio components."""
        try:
            self._recorder = AudioRecorder(
                sample_rate=16000,
                channels=1,
                device=None
            )
            self._vad = VoiceActivityDetector(
                energy_threshold=0.02,
                silence_frames=30
            )
            self._logger.info("Audio components initialized")
        except STTError as e:
            self._logger.warning(f"Audio not available: {e}")
            self._recorder = None

    def _initialize_input(self):
        """Initialize input provider."""
        try:
            if KeydProvider().is_available():
                self._input_provider = KeydProvider(ConfigManager())
                self._logger.info("Using keyd input provider")
            elif EvdevProvider().is_available():
                self._input_provider = EvdevProvider()
                self._logger.info("Using evdev input provider")
            else:
                self._logger.warning("No input provider available")
        except Exception as e:
            self._logger.warning(f"Input provider error: {e}")

    def _initialize_router(self):
        """Initialize router."""
        try:
            self._router = Router(
                fast_llm=None,
                strong_llm=None,
                config={}
            )
            self._streaming_router = StreamingRouter(
                router=self._router,
                config={}
            )
            self._logger.info("Router initialized")
        except Exception as e:
            self._logger.warning(f"Router initialization error: {e}")

    def _initialize_output(self):
        """Initialize output components."""
        try:
            backend = DesktopRegistry.detect_best_backend()
            self._executor = ActionExecutor(backend)
            self._logger.info(f"Output backend: {backend.get_name()}")
        except Exception as e:
            self._logger.warning(f"Output initialization error: {e}")

    def _initialize_overlay(self):
        """Initialize overlay."""
        try:
            self._overlay = create_overlay(self.config)
            self._logger.info("Overlay initialized")
        except Exception as e:
            self._logger.warning(f"Overlay initialization error: {e}")

    def start_recording(self):
        """Start audio recording (for hold-to-talk mode)."""
        if self._recording:
            return

        if not self._recorder:
            self._logger.error("Audio recorder not available")
            return

        self._recording = True
        self._state = AppState.RECORDING
        self._logger.info("Recording started")

        try:
            self._recorder.start_recording()
            if self._overlay:
                self._overlay.set_recording("Recording...")
            if self._event_callback:
                self._event_callback("recording_started")
        except Exception as e:
            self._logger.error(f"Failed to start recording: {e}")
            self._recording = False
            self._state = AppState.ERROR

    def stop_recording(self):
        """Stop audio recording and process the audio."""
        if not self._recording:
            return

        self._recording = False
        self._state = AppState.PROCESSING
        self._logger.info("Recording stopped, processing...")

        try:
            if self._overlay:
                self._overlay.set_processing("Processing...")

            recording = self._recorder.stop_recording()

            if recording is None or recording.duration < 0.1:
                self._logger.info("Recording too short, ignoring")
                self._state = AppState.IDLE
                if self._overlay:
                    self._overlay.set_idle()
                return

            if self._event_callback:
                self._event_callback("recording_stopped")

            self._process_audio_async(recording)

        except Exception as e:
            self._logger.error(f"Failed to stop recording: {e}")
            self._state = AppState.ERROR
            if self._overlay:
                self._overlay.set_error(str(e))

    def _process_audio_async(self, recording):
        """Process audio in a background thread."""
        def process():
            try:
                wav_bytes = recording.to_wav_bytes()

                stt_provider = GroqWhisperProvider(self.config)
                if not stt_provider.is_available():
                    self._logger.error("STT provider not available")
                    self._state = AppState.ERROR
                    return

                transcript = stt_provider.transcribe(wav_bytes)

                if not transcript or not transcript.strip():
                    self._logger.info("Empty transcript")
                    self._state = AppState.IDLE
                    return

                self._logger.info(f"Transcript: {transcript}")

                if self._transcript_callback:
                    self._transcript_callback(transcript)

                if self._router:
                    route_output = self._router.route(transcript)

                    if self._executor and route_output.actions:
                        for action in route_output.actions:
                            try:
                                self._executor.execute(action)
                            except Exception as e:
                                self._logger.error(f"Action execution failed: {e}")

                self._state = AppState.RESULT
                if self._overlay:
                    self._overlay.set_result(transcript)

                if self._event_callback:
                    self._event_callback("transcription_complete", transcript)

            except Exception as e:
                self._logger.error(f"Audio processing failed: {e}")
                self._state = AppState.ERROR
                if self._overlay:
                    self._overlay.set_error(str(e))
                if self._event_callback:
                    self._event_callback("error", str(e))

        thread = Thread(target=process, daemon=True)
        thread.start()

    def start_hotkey_listening(self, callback: Optional[Callable] = None):
        """Start listening for hotkey events."""
        if not self._input_provider:
            raise CapabilityUnavailable("No input provider available")

        self._event_callback = callback

        def handle_event(event):
            if hasattr(event, 'key'):
                key = event.key.upper()
                state = event.state

                if key == 'F24':
                    if state == 'down':
                        self._key_pressed = True
                        self._logger.debug("F24 pressed")
                        self.start_recording()
                    elif state == 'up':
                        self._key_pressed = False
                        self._logger.debug("F24 released")
                        if self._hold_mode:
                            self.stop_recording()
            elif hasattr(event, 'code'):
                if event.code == 107:
                    if event.is_key_down:
                        self._key_pressed = True
                        self._logger.debug("F24 pressed (evdev)")
                        self.start_recording()
                    elif event.is_key_up:
                        self._key_pressed = False
                        self._logger.debug("F24 released (evdev)")
                        if self._hold_mode:
                            self.stop_recording()

        try:
            self._input_provider.start_listening(handle_event)
            self._logger.info("Hotkey listening started")
        except Exception as e:
            raise CapabilityUnavailable(f"Failed to start listening: {e}")

    def stop_hotkey_listening(self):
        """Stop listening for hotkey events."""
        if self._input_provider:
            self._input_provider.stop_listening()
            self._logger.info("Hotkey listening stopped")

    def set_transcript_callback(self, callback: Callable[[str], None]):
        """Set callback for transcript results."""
        self._transcript_callback = callback

    def set_event_callback(self, callback: Callable):
        """Set callback for state changes."""
        self._event_callback = callback

    def get_state(self) -> str:
        """Get current application state."""
        return self._state

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    def get_audio_devices(self) -> list:
        """Get available audio input devices."""
        return detect_audio_devices()

    def diagnostics(self) -> Dict[str, Any]:
        """Get application diagnostics."""
        return {
            "state": self._state,
            "recording": self._recording,
            "hold_mode": self._hold_mode,
            "audio_available": self._recorder is not None,
            "input_available": self._input_provider is not None,
            "router_available": self._router is not None,
            "output_available": self._executor is not None,
            "overlay_available": self._overlay is not None,
            "audio_devices": self.get_audio_devices() if self._recorder else [],
        }


def create_app(config: Optional[GhostTypeConfig] = None) -> GhostTypeDesktopApp:
    """Create and return a GhostTypeDesktopApp instance."""
    return GhostTypeDesktopApp(config)
