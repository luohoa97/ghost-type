"""WAV file handling for GhostType."""
import wave
import io
import struct
from typing import Optional, List, Tuple
import numpy as np
from ghosttype.core.errors import STTError


def create_wav_bytes(samples: np.ndarray, sample_rate: int, channels: int = 1) -> bytes:
    """Create WAV file bytes from audio samples."""
    # Ensure mono
    if len(samples.shape) > 1:
        samples = samples.mean(axis=1)
    
    # Convert to 16-bit PCM
    samples = np.clip(samples * 32767, -32768, 32767).astype(np.int16)
    
    # Create WAV in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    
    return buffer.getvalue()


def save_wav_file(samples: np.ndarray, sample_rate: int, filepath: str, channels: int = 1):
    """Save audio samples to WAV file."""
    wav_bytes = create_wav_bytes(samples, sample_rate, channels)
    
    with open(filepath, 'wb') as f:
        f.write(wav_bytes)


def load_wav_file(filepath: str) -> Tuple[np.ndarray, int]:
    """Load audio from WAV file."""
    try:
        with wave.open(filepath, 'rb') as wf:
            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            
            # Convert to numpy array
            samples = np.frombuffer(audio_data, dtype=np.int16)
            
            # Convert to float and normalize
            samples = samples.astype(np.float32) / 32768.0
            
            # Handle stereo
            if n_channels > 1:
                samples = samples.reshape(-1, n_channels)
            
            return samples, sample_rate
    except wave.Error as e:
        raise STTError(f"Failed to read WAV file: {e}")
    except FileNotFoundError:
        raise STTError(f"WAV file not found: {filepath}")


def wav_duration(wav_bytes: bytes) -> float:
    """Calculate duration of WAV data in seconds."""
    with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
        n_frames = wf.getnframes()
        sample_rate = wf.getframerate()
        return n_frames / sample_rate


def resample_wav(wav_bytes: bytes, target_sample_rate: int) -> bytes:
    """Resample WAV data to target sample rate."""
    import scipy.signal
    
    with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        n_frames = wf.getnframes()
        audio_data = wf.readframes(n_frames)
        
        # Convert to numpy array
        samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        if n_channels > 1:
            samples = samples.reshape(-1, n_channels)
        
        # Resample
        num_samples = int(len(samples) * target_sample_rate / sample_rate)
        if n_channels > 1:
            resampled = scipy.signal.resample(samples, num_samples, axis=0)
        else:
            resampled = scipy.signal.resample(samples, num_samples)
        
        # Convert back to 16-bit PCM
        resampled = np.clip(resampled * 32767, -32768, 32767).astype(np.int16)
        
        # Create new WAV
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(2)
            wf.setframerate(target_sample_rate)
            wf.writeframes(resampled.tobytes())
        
        return buffer.getvalue()


def split_wav_by_silence(wav_bytes: bytes, silence_threshold: float = 0.01, min_silence_duration: float = 0.5) -> List[bytes]:
    """Split WAV data into segments based on silence."""
    from ghosttype.ghosttype_desktop.audio.vad import EnergyBasedVAD
    
    with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        audio_data = wf.readframes(n_frames)
        
        # Convert to numpy array
        samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Detect speech segments
        vad = EnergyBasedVAD(sample_rate=sample_rate)
        segments = vad.process_audio(samples)
        
        # Split WAV at segment boundaries
        segments_wav = []
        frame_size = int(sample_rate * 0.03)  # 30ms frames
        
        for start, end in segments:
            start_idx = int(start * sample_rate)
            end_idx = int(end * sample_rate)
            
            segment_samples = samples[start_idx:end_idx]
            segment_wav = create_wav_bytes(segment_samples, sample_rate)
            segments_wav.append(segment_wav)
        
        return segments_wav


def merge_wav_bytes(wav_bytes_list: List[bytes]) -> bytes:
    """Merge multiple WAV bytes into a single WAV."""
    if not wav_bytes_list:
        return b''
    
    # Get parameters from first WAV
    with wave.open(io.BytesIO(wav_bytes_list[0]), 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sample_rate = wf.getframerate()
    
    # Concatenate all audio data
    all_data = b''
    for wav_bytes in wav_bytes_list:
        with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
            all_data += wf.readframes(wf.getnframes())
    
    # Create merged WAV
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(all_data)
    
    return buffer.getvalue()
