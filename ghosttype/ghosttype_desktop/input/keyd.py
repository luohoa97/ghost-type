"""Keyd input provider for GhostType."""
import os
import select
import struct
import subprocess
import time
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from threading import Thread, Event

from ghosttype.core.errors import DependencyMissing, CapabilityUnavailable
from ghosttype.core.config import ConfigManager


@dataclass
class KeydEvent:
    """Represents a keyd event."""
    key: str
    state: str
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class KeydProvider:
    """Input provider using keyd daemon."""

    VOICE_KEY_CODES = {
        "CapsLock": 58,
        "F24": 107,
        "F22": 105,
        "F23": 106,
    }
    KEY_MAP = {
        58: "CapsLock",
        57: "Space",
        28: "Enter",
        1: "Escape",
        107: "F24",
    }

    def __init__(self, config: Optional[ConfigManager] = None, voice_key: Optional[str] = None):
        self.config = config or ConfigManager()
        self.config.load()

        self._voice_key = voice_key or self.config.config.hotkeys.voice_key
        self._voice_key_code = self.VOICE_KEY_CODES.get(self._voice_key, 58)
        self._cancel_key = self.config.config.hotkeys.cancel_key
        self._ocr_key = self.config.config.hotkeys.ocr_key
        self._record_mode = self.config.config.hotkeys.record_mode

        self._running = False
        self._event_callback: Optional[Callable[[KeydEvent], None]] = None
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._use_evdev_fallback = False

        self._check_dependencies()

    def _check_dependencies(self):
        """Check if keyd is available."""
        if not self._find_keyd_config():
            raise DependencyMissing(
                "keyd configuration not found. "
                "Install keyd and run: ghosttype keyd install-config"
            )

    def _find_keyd_config(self) -> Optional[str]:
        """Find keyd configuration file."""
        config_paths = [
            "/etc/keyd/ghosttype.conf",
            "/etc/keyd.conf",
            os.path.expanduser("~/.config/keyd/ghosttype.conf"),
        ]

        for path in config_paths:
            if os.path.exists(path):
                return path

        return None

    def _get_keyd_config_path(self) -> str:
        """Get the path to the keyd config file."""
        return self.config.get_path("config") / "ghosttype.conf"

    def get_config_content(self) -> str:
        """Get the keyd configuration content."""
        voice_key = self._voice_key
        if voice_key == "F24":
            return """[ids]
*

[main]
capslock = f24
"""
        elif voice_key == "CapsLock":
            return """[ids]
*

[main]
capslock = f24
"""
        elif voice_key == "F22":
            return """[ids]
*

[main]
f22 = f24
"""
        elif voice_key == "F23":
            return """[ids]
*

[main]
f23 = f24
"""
        else:
            return f"""[ids]
*

[main]
{voice_key.lower()} = f24
"""

    def is_available(self) -> bool:
        """Check if keyd is available."""
        try:
            subprocess.run(["which", "keyd"], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_running(self) -> bool:
        """Check if keyd service is running."""
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "keyd"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == "active"
        except FileNotFoundError:
            try:
                result = subprocess.run(
                    ["service", "keyd", "status"],
                    capture_output=True,
                    text=True
                )
                return "running" in result.stdout.lower()
            except FileNotFoundError:
                return False

    def start_listening(self, callback: Callable[[KeydEvent], None]):
        """Start listening for keyd events."""
        if not self.is_available():
            raise CapabilityUnavailable(
                "keyd is not available. Install keyd and run: ghosttype keyd install-config"
            )

        self._event_callback = callback
        self._running = True
        self._stop_event.clear()

        self._thread = Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def _listen_loop(self):
        """Main listening loop using direct evdev access."""
        self._use_evdev_fallback = True
        self._poll_evdev_events()

    def _poll_evdev_events(self):
        """Poll /dev/input/event* directly for F24 key events."""
        devices = self._find_input_devices()

        if not devices:
            return

        while self._running and not self._stop_event.is_set():
            try:
                rlist, _, _ = select.select(devices, [], [], 0.05)

                for fd in rlist:
                    try:
                        data = os.read(fd, 24)
                        if len(data) == 24:
                            self._process_evdev_raw(data)
                    except (OSError, IOError):
                        continue

            except Exception:
                continue

    def _process_evdev_raw(self, data: bytes):
        """Process raw evdev event data."""
        if len(data) < 24:
            return

        tv_sec, tv_usec, event_type, code, value = struct.unpack('llHHI', data[:24])

        if event_type == 1:
            key_name = self.KEY_MAP.get(code, None)

            if key_name is None and code == self._voice_key_code:
                key_name = self._voice_key

            if key_name:
                state = "down" if value == 1 else "up"
                event = KeydEvent(key=key_name, state=state, timestamp=tv_sec + tv_usec / 1000000.0)

                if self._event_callback:
                    try:
                        self._event_callback(event)
                    except Exception:
                        pass

    def _find_input_devices(self) -> List:
        """Find readable input event devices."""
        devices = []
        for i in range(32):
            device_path = f"/dev/input/event{i}"
            if os.path.exists(device_path):
                try:
                    fd = os.open(device_path, os.O_RDONLY | os.O_NONBLOCK)
                    devices.append(fd)
                except (PermissionError, OSError):
                    pass
        return devices

    def stop_listening(self):
        """Stop listening for key events."""
        self._running = False
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def install_config(self) -> str:
        """Install keyd configuration."""
        config_content = self.get_config_content()
        config_path = "/etc/keyd/ghosttype.conf"

        if os.path.exists("/etc/keyd") and os.access("/etc/keyd", os.W_OK):
            with open(config_path, 'w') as f:
                f.write(config_content)
            return f"Config written to {config_path}"
        else:
            return (
                f"Run the following commands to install keyd config:\n"
                f"  sudo mkdir -p /etc/keyd\n"
                f"  sudo cp ghosttype/keyd/ghosttype.conf /etc/keyd/\n"
                f"  sudo systemctl restart keyd"
            )

    def diagnostics(self) -> Dict[str, Any]:
        """Get diagnostics for keyd provider."""
        return {
            "available": self.is_available(),
            "running": self.is_running(),
            "config_path": self._find_keyd_config(),
            "voice_key": self._voice_key,
            "voice_key_code": self._voice_key_code,
            "record_mode": self._record_mode,
            "cancel_key": self._cancel_key,
            "ocr_key": self._ocr_key,
        }


class KeydDaemon:
    """Manages the keyd daemon."""

    def __init__(self):
        self._config = ConfigManager()
        self._config.load()

    def start(self) -> bool:
        """Start the keyd daemon."""
        try:
            subprocess.run(
                ["systemctl", "--user", "start", "keyd"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def stop(self) -> bool:
        """Stop the keyd daemon."""
        try:
            subprocess.run(
                ["systemctl", "--user", "stop", "keyd"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def restart(self) -> bool:
        """Restart the keyd daemon."""
        try:
            subprocess.run(
                ["systemctl", "--user", "restart", "keyd"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def status(self) -> str:
        """Get keyd daemon status."""
        try:
            result = subprocess.run(
                ["systemctl", "--user", "status", "keyd"],
                capture_output=True,
                text=True
            )
            return result.stdout
        except FileNotFoundError:
            return "systemctl not found"

    def is_running(self) -> bool:
        """Check if keyd is running."""
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "keyd"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == "active"
        except FileNotFoundError:
            return False
