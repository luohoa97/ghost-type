"""Voice Activity Detection module."""
import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass
import time


@dataclass
class VADResult:
    """Result of VAD processing."""
    is_speech: bool
    energy: float
    timestamp: float = field(default_factory=time.time)


class EnergyBasedVAD:
    """Voice Activity Detection using energy threshold."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration: float = 0.03,  # 30ms frames
        energy_threshold: float = 0.01,
        silence_duration: float = 0.5,
        pre_speech_buffer: float = 0.2
    ):
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.pre_speech_buffer = pre_speech_buffer
        
        self._frame_size = int(sample_rate * frame_duration)
        self._silence_frames = int(silence_duration / frame_duration)
        self._pre_speech_frames = int(pre_speech_buffer / frame_duration)
        
        self._reset()
    
    def _reset(self):
        """Reset VAD state."""
        self._speech_frames = 0
        self._silence_frames_count = 0
        self._buffer: List[np.ndarray] = []
        self._last_speech_time: Optional[float] = None
        self._in_speech = False
    
    def process_frame(self, frame: np.ndarray, timestamp: Optional[float] = None) -> VADResult:
        """Process a single audio frame."""
        if timestamp is None:
            timestamp = time.time()
        
        # Calculate energy (RMS)
        energy = np.sqrt(np.mean(frame ** 2))
        is_speech = energy > self.energy_threshold
        
        if is_speech:
            self._speech_frames += 1
            self._silence_frames_count = 0
            self._last_speech_time = timestamp
            
            if not self._in_speech:
                self._in_speech = True
                # Include pre-speech buffer
                buffer_frames = int(self.pre_speech_buffer / self.frame_duration)
                start_idx = max(0, len(self._buffer) - buffer_frames)
                buffered_audio = np.concatenate(self._buffer[start_idx:]) if self._buffer else np.array([])
                buffered_audio = np.concatenate([buffered_audio, frame])
            else:
                buffered_audio = frame
            
            return VADResult(is_speech=True, energy=energy, timestamp=timestamp)
        else:
            self._silence_frames_count += 1
            
            if self._in_speech and self._silence_frames_count >= self._silence_frames:
                self._in_speech = False
                return VADResult(is_speech=False, energy=energy, timestamp=timestamp)
            
            return VADResult(is_speech=False, energy=energy, timestamp=timestamp)
    
    def process_audio(self, audio: np.ndarray) -> List[Tuple[float, float]]:
        """Process audio and return speech segments as (start, end) timestamps."""
        frame_size = self._frame_size
        segments = []
        current_start: Optional[float] = None
        
        for i in range(0, len(audio), frame_size):
            frame = audio[i:i + frame_size]
            if len(frame) < frame_size:
                break
            
            result = self.process_frame(frame)
            
            if result.is_speech and current_start is None:
                current_start = i / self.sample_rate
            elif not result.is_speech and current_start is not None:
                segments.append((current_start, (i + frame_size) / self.sample_rate))
                current_start = None
        
        if current_start is not None:
            segments.append((current_start, len(audio) / self.sample_rate))
        
        return segments
    
    def reset(self):
        """Reset VAD state."""
        self._reset()


class SpectralVAD:
    """Voice Activity Detection using spectral features."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration: float = 0.03,
        spectral_threshold: float = 0.7,
        zero_crossing_threshold: float = 0.1
    ):
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.spectral_threshold = spectral_threshold
        self.zero_crossing_threshold = zero_crossing_threshold
        
        self._frame_size = int(sample_rate * frame_duration)
        self._reset()
    
    def _reset(self):
        """Reset VAD state."""
        self._speech_count = 0
        self._total_frames = 0
    
    def _calculate_spectral_centroid(self, frame: np.ndarray) -> float:
        """Calculate spectral centroid of a frame."""
        # Simple spectral analysis using FFT
        fft = np.fft.rfft(frame * np.hanning(len(frame)))
        magnitude = np.abs(fft)
        
        if np.sum(magnitude) == 0:
            return 0.0
        
        freqs = np.fft.rfftfreq(len(frame), 1.0 / self.sample_rate)
        centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
        return centroid
    
    def _calculate_zero_crossing_rate(self, frame: np.ndarray) -> float:
        """Calculate zero crossing rate."""
        threshold = np.mean(np.abs(frame)) * 0.1
        centered = frame - np.mean(frame)
        centered = np.where(np.abs(centered) < threshold, 0, centered)
        
        crossings = np.sum(np.abs(np.diff(np.sign(centered))) > 0)
        return crossings / (2 * len(frame))
    
    def is_speech(self, frame: np.ndarray) -> bool:
        """Determine if frame contains speech."""
        centroid = self._calculate_spectral_centroid(frame)
        zcr = self._calculate_zero_crossing_rate(frame)
        
        # Speech typically has moderate spectral centroid and higher ZCR
        spectral_score = min(centroid / 1000, 1.0)  # Normalize to 0-1
        zcr_score = min(zcr / 0.1, 1.0)  # Normalize to 0-1
        
        combined_score = 0.6 * spectral_score + 0.4 * zcr_score
        return combined_score > self.spectral_threshold
    
    def process_audio(self, audio: np.ndarray) -> List[Tuple[int, int]]:
        """Process audio and return speech frame indices."""
        frame_size = self._frame_size
        speech_frames = []
        current_segment: Optional[Tuple[int, int]] = None
        
        for i in range(0, len(audio), frame_size):
            frame = audio[i:i + frame_size]
            if len(frame) < frame_size:
                break
            
            is_speech = self.is_speech(frame)
            
            if is_speech:
                start_frame = i // frame_size
                if current_segment is None:
                    current_segment = [start_frame, start_frame + 1]
                else:
                    current_segment[1] = start_frame + 1
            else:
                if current_segment is not None:
                    speech_frames.append(tuple(current_segment))
                    current_segment = None
        
        if current_segment is not None:
            speech_frames.append(tuple(current_segment))
        
        return speech_frames
    
    def reset(self):
        """Reset VAD state."""
        self._reset()
