"""Audio recording module for GhostType."""
import sounddevice as sd
import numpy as np
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass
from threading import Event
import time
import wave
import io
from ghosttype.core.errors import STTError


@dataclass
class AudioRecording:
    """Represents an audio recording."""
    samples: np.ndarray
    sample_rate: int
    channels: int
    duration: float
    
    def to_wav_bytes(self) -> bytes:
        """Convert recording to WAV bytes."""
        # Ensure mono
        if len(self.samples.shape) > 1:
            samples = self.samples.mean(axis=1)
        else:
            samples = self.samples
        
        # Convert to 16-bit PCM
        samples = np.clip(samples * 32767, -32768, 32767).astype(np.int16)
        
        # Create WAV in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(samples.tobytes())
        
        return buffer.getvalue()


class AudioRecorder:
    """Records audio from the default input device."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device: Optional[int] = None,
        dtype: str = "float32"
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.dtype = dtype
        
        self._recording = False
        self._samples: List[np.ndarray] = []
        self._stop_event = Event()
        self._stream: Optional[sd.InputStream] = None
        
        # Check availability
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if audio dependencies are available."""
        try:
            import sounddevice
        except ImportError:
            raise STTError(
                "sounddevice package is required for audio recording. "
                "Install with: uv add sounddevice"
            )
    
    def _get_device_info(self) -> Dict[str, Any]:
        """Get information about the audio input device."""
        try:
            if self.device is None:
                default = sd.default.device
                return {
                    "input": default[0],
                    "output": default[1],
                    "sample_rate": self.sample_rate
                }
            return {"device": self.device}
        except Exception as e:
            raise STTError(f"Failed to get audio device info: {e}")
    
    def start_recording(self):
        """Start recording audio."""
        if self._recording:
            return
        
        self._recording = True
        self._samples = []
        self._stop_event.clear()
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            if self._recording:
                self._samples.append(indata.copy())
        
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                device=self.device,
                callback=callback,
                blocksize=1024
            )
            self._stream.start()
        except sd.PortAudioError as e:
            raise STTError(f"Failed to start audio recording: {e}")
    
    def stop_recording(self) -> Optional[AudioRecording]:
        """Stop recording and return the audio."""
        if not self._recording:
            return None
        
        self._recording = False
        
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        
        if not self._samples:
            return None
        
        # Concatenate all samples
        audio_data = np.concatenate(self._samples, axis=0)
        
        # Calculate duration
        duration = len(audio_data) / self.sample_rate
        
        return AudioRecording(
            samples=audio_data,
            sample_rate=self.sample_rate,
            channels=self.channels,
            duration=duration
        )
    
    def is_recording(self) -> bool:
        """Check if recording is in progress."""
        return self._recording
    
    def get_recording_duration(self) -> float:
        """Get current recording duration in seconds."""
        if not self._samples:
            return 0.0
        total_samples = sum(len(s) for s in self._samples)
        return total_samples / self.sample_rate
    
    def reset(self):
        """Reset the recorder."""
        self.stop_recording()
        self._samples = []


class VAD:
    """Voice Activity Detection using energy threshold."""
    
    def __init__(self, threshold: float = 0.01, min_silence: float = 0.5):
        self.threshold = threshold
        self.min_silence = min_silence
        self._last_speech_time: Optional[float] = None
    
    def is_speech(self, audio: np.ndarray) -> bool:
        """Check if audio contains speech based on energy level."""
        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio ** 2))
        return energy > self.threshold
    
    def update(self, audio: np.ndarray, timestamp: float) -> bool:
        """Update VAD state and return True if silence detected."""
        if self.is_speech(audio):
            self._last_speech_time = timestamp
            return False
        
        if self._last_speech_time is not None:
            silence_duration = timestamp - self._last_speech_time
            if silence_duration >= self.min_silence:
                return True
        
        return False
    
    def reset(self):
        """Reset VAD state."""
        self._last_speech_time = None


def detect_audio_devices() -> List[Dict[str, Any]]:
    """Detect available audio input devices."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    "id": i,
                    "name": device['name'],
                    "max_input_channels": device['max_input_channels'],
                    "default_samplerate": device.get('default_samplerate', 44100)
                })
        
        return input_devices
    except Exception:
        return []


def get_default_audio_device() -> Optional[int]:
    """Get the default audio input device ID."""
    try:
        import sounddevice as sd
        default = sd.default.device
        if default and default[0] >= 0:
            return default[0]
    except Exception:
        pass
    return None
