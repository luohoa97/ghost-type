"""Keyd input provider for GhostType."""
import os
import subprocess
import time
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from threading import Thread, Event
import signal

from ghosttype.core.errors import DependencyMissing, CapabilityUnavailable
from ghosttype.core.config import ConfigManager


@dataclass
class KeydEvent:
    """Represents a keyd event."""
    key: str
    state: str  # "down" or "up"
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class KeydProvider:
    """Input provider using keyd daemon."""
    
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.config.load()
        
        self._hotkey = self.config.config.hotkeys.voice_key
        self._cancel_key = self.config.config.hotkeys.cancel_key
        self._ocr_key = self.config.config.hotkeys.ocr_key
        self._record_mode = self.config.config.hotkeys.record_mode
        
        self._running = False
        self._event_callback: Optional[Callable[[KeydEvent], None]] = None
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        
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
        voice_key = self._hotkey
        if voice_key == "F24":
            # Map CapsLock to F24
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
            # Try alternative method
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
        """Main listening loop."""
        # Use udevadm to monitor key events
        try:
            process = subprocess.Popen(
                ["udevadm", "monitor", "-u", "-s", "input"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            while self._running and not self._stop_event.is_set():
                line = process.stdout.readline()
                if line:
                    self._process_event(line)
                    
        except FileNotFoundError:
            # Fallback: poll /dev/input events
            self._poll_input_events()
    
    def _process_event(self, line: str):
        """Process a udev event line."""
        # Parse key event from udev output
        if "key" in line.lower():
            # Extract key information
            key = self._extract_key_from_line(line)
            if key:
                state = "down" if "press" in line.lower() else "up"
                event = KeydEvent(key=key, state=state)
                if self._event_callback:
                    self._event_callback(event)
    
    def _extract_key_from_line(self, line: str) -> Optional[str]:
        """Extract key name from udev line."""
        # This is a simplified implementation
        # In practice, you'd parse the full udev event
        if "f24" in line.lower():
            return "F24"
        elif "escape" in line.lower():
            return "Escape"
        return None
    
    def _poll_input_events(self):
        """Poll input events as fallback."""
        import select
        
        input_devices = self._find_input_devices()
        
        while self._running and not self._stop_event.is_set():
            for device in input_devices:
                try:
                    with open(device, 'rb') as f:
                        rlist, _, _ = select.select([f], [], [], 0.1)
                        if rlist:
                            data = f.read(24)  # evdev event size
                            if len(data) == 24:
                                self._process_evdev_event(data)
                except (PermissionError, FileNotFoundError):
                    continue
    
    def _find_input_devices(self) -> List[str]:
        """Find input event devices."""
        devices = []
        for i in range(32):
            device = f"/dev/input/event{i}"
            if os.path.exists(device):
                devices.append(device)
        return devices
    
    def _process_evdev_event(self, data: bytes):
        """Process an evdev event."""
        # Parse evdev event structure
        # struct input_event {
        #     struct timeval time;
        #     unsigned short type;
        #     unsigned short code;
        #     unsigned int value;
        # };
        
        if len(data) < 24:
            return
        
        # Extract event fields (little-endian)
        import struct
        tv_sec, tv_usec, event_type, code, value = struct.unpack('llHHI', data[:24])
        
        if event_type == 1:  # EV_KEY
            key_map = {
                58: "CapsLock",
                57: "Space",
                28: "Enter",
                1: "Escape",
            }
            
            key_name = key_map.get(code, f"KEY_{code}")
            state = "down" if value == 1 else "up"
            
            event = KeydEvent(key=key_name, state=state)
            if self._event_callback:
                self._event_callback(event)
    
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
        
        # Check if we have permission
        if os.path.exists("/etc/keyd") and os.access("/etc/keyd", os.W_OK):
            with open(config_path, 'w') as f:
                f.write(config_content)
            return f"Config written to {config_path}"
        else:
            # Need sudo
            return (
                f"Run the following commands to install keyd config:\n"
                f"  sudo mkdir -p /etc/keyd\n"
                f"  echo '{config_content}' | sudo tee /etc/keyd/ghosttype.conf\n"
                f"  sudo systemctl restart keyd"
            )
    
    def diagnostics(self) -> Dict[str, Any]:
        """Get diagnostics for keyd provider."""
        return {
            "available": self.is_available(),
            "running": self.is_running(),
            "config_path": self._find_keyd_config(),
            "hotkey": self._hotkey,
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
