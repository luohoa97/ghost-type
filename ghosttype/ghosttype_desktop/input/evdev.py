"""Evdev input provider for GhostType."""
import os
import select
import struct
import time
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from threading import Thread, Event

from ghosttype.core.errors import DependencyMissing, CapabilityUnavailable


@dataclass
class EvdevEvent:
    """Represents an evdev event."""
    device: str
    event_type: int
    code: int
    value: int
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    @property
    def is_key_event(self) -> bool:
        """Check if this is a key event."""
        return self.event_type == 1

    @property
    def is_key_down(self) -> bool:
        """Check if this is a key down event."""
        return self.is_key_event and self.value == 1

    @property
    def is_key_up(self) -> bool:
        """Check if this is a key up event."""
        return self.is_key_event and self.value == 0


class EvdevProvider:
    """Input provider using evdev (Linux input subsystem)."""

    VOICE_KEY_CODES = {
        "CapsLock": 58,
        "F24": 107,
        "F22": 105,
        "F23": 106,
    }
    KEY_CODES = {
        58: "CapsLock",
        57: "Space",
        28: "Enter",
        1: "Escape",
        59: "F1",
        60: "F2",
        61: "F3",
        62: "F4",
        63: "F5",
        64: "F6",
        65: "F7",
        66: "F8",
        67: "F9",
        68: "F10",
        87: "F11",
        88: "F12",
        96: "F13",
        97: "F14",
        98: "F15",
        99: "F16",
        100: "F17",
        101: "F18",
        102: "F19",
        103: "F20",
        104: "F21",
        105: "F22",
        106: "F23",
        107: "F24",
    }

    def __init__(self, voice_key: str = "F24"):
        self._voice_key = voice_key
        self._voice_key_code = self.VOICE_KEY_CODES.get(voice_key, 58)
        self._running = False
        self._event_callback: Optional[Callable[[EvdevEvent], None]] = None
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._devices: List = []
        self._device_paths: List[str] = []

        self._check_permissions()

    def _check_permissions(self):
        """Check if we have permission to read input devices."""
        has_devices = False
        for i in range(32):
            device = f"/dev/input/event{i}"
            if os.path.exists(device):
                has_devices = True
                if not os.access(device, os.R_OK):
                    raise DependencyMissing(
                        f"No read permission for {device}. "
                        "Add user to input group: sudo usermod -a -G input $USER"
                    )

        if not has_devices:
            raise DependencyMissing(
                "No input devices found. "
                "Check that /dev/input/event* files exist."
            )

    def _find_input_devices(self) -> List:
        """Find all readable input event devices."""
        devices = []
        paths = []
        for i in range(32):
            device = f"/dev/input/event{i}"
            if os.path.exists(device) and os.access(device, os.R_OK):
                try:
                    fd = os.open(device, os.O_RDONLY | os.O_NONBLOCK)
                    devices.append(fd)
                    paths.append(device)
                except (PermissionError, OSError):
                    pass
        self._devices = devices
        self._device_paths = paths
        return devices

    def _get_key_name(self, code: int) -> str:
        """Get key name from key code."""
        return self.KEY_CODES.get(code, f"KEY_{code}")

    def start_listening(self, callback: Callable[[EvdevEvent], None]):
        """Start listening for evdev events."""
        self._event_callback = callback
        self._running = True
        self._stop_event.clear()
        self._find_input_devices()

        self._thread = Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def _listen_loop(self):
        """Main listening loop."""
        while self._running and not self._stop_event.is_set():
            try:
                if not self._devices:
                    self._find_input_devices()
                    if not self._devices:
                        time.sleep(0.1)
                        continue

                rlist, _, _ = select.select(self._devices, [], [], 0.05)

                for fd in rlist:
                    try:
                        data = os.read(fd, 24)
                        if len(data) == 24:
                            device_path = self._device_paths[self._devices.index(fd)]
                            event = self._parse_evdev_event(data, device_path)
                            if event and self._event_callback:
                                self._event_callback(event)
                    except (OSError, IOError, ValueError):
                        continue

            except Exception:
                continue

    def _parse_evdev_event(self, data: bytes, device: str) -> Optional[EvdevEvent]:
        """Parse an evdev event."""
        if len(data) < 24:
            return None

        tv_sec, tv_usec = struct.unpack('ll', data[:8])
        event_type, code, value = struct.unpack('HHI', data[8:20])

        return EvdevEvent(
            device=device,
            event_type=event_type,
            code=code,
            value=value,
            timestamp=tv_sec + tv_usec / 1000000.0
        )

    def stop_listening(self):
        """Stop listening for events."""
        self._running = False
        self._stop_event.set()

        for fd in self._devices:
            try:
                os.close(fd)
            except OSError:
                pass
        self._devices = []
        self._device_paths = []

        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def is_available(self) -> bool:
        """Check if evdev is available."""
        try:
            self._find_input_devices()
            return len(self._devices) > 0
        except DependencyMissing:
            return False

    def diagnostics(self) -> Dict[str, Any]:
        """Get diagnostics for evdev provider."""
        self._find_input_devices()
        return {
            "available": self.is_available(),
            "device_count": len(self._devices),
            "devices": self._device_paths,
            "voice_key": self._voice_key,
            "voice_key_code": self._voice_key_code,
        }


class EvdevMonitor:
    """Monitor for evdev events."""

    def __init__(self):
        self._provider = EvdevProvider()
        self._events: List[EvdevEvent] = []

    def start(self):
        """Start monitoring."""
        def callback(event: EvdevEvent):
            self._events.append(event)

        self._provider.start_listening(callback)

    def stop(self):
        """Stop monitoring."""
        self._provider.stop_listening()

    def get_events(self) -> List[EvdevEvent]:
        """Get collected events."""
        return self._events.copy()

    def clear_events(self):
        """Clear collected events."""
        self._events.clear()
