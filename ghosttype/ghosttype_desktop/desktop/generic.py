import os
import shutil
import subprocess
from typing import List, Optional, Dict, Any
from .base import DesktopBackend, Capability
from ghosttype.core.errors import DesktopBackendError

class GenericClipboardBackend(DesktopBackend):
    def detect(self) -> bool:
        return True # Always available as a base fallback

    def get_name(self) -> str:
        return "GenericClipboard"

    def capabilities(self) -> List[Capability]:
        caps = []
        if self._find_clipboard_tool():
            caps.extend([Capability.READ_CLIPBOARD, Capability.WRITE_CLIPBOARD])
        if shutil.which("notify-send"):
            caps.append(Capability.NOTIFICATIONS)
        return caps

    def score(self) -> int:
        return 10 # Lowest possible score

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "clipboard_tool": self._find_clipboard_tool(),
            "notify_tool": shutil.which("notify-send")
        }

    def _find_clipboard_tool(self) -> Optional[str]:
        for tool in ["wl-copy", "xclip", "xsel"]:
            if shutil.which(tool):
                return tool
        return None

    def paste_text(self, text: str):
        self.write_clipboard(text)
        self.notify("GhostType", "Text copied to clipboard. Please paste manually.")

    def type_text(self, text: str):
        self.paste_text(text)

    def press_key(self, key: str):
        raise DesktopBackendError(f"press_key not supported by {self.get_name()}")

    def read_clipboard(self) -> Optional[str]:
        tool = self._find_clipboard_tool()
        if tool == "wl-paste" or tool == "wl-copy": # wl-paste is usually part of wl-clipboard
            if shutil.which("wl-paste"):
                return subprocess.check_output(["wl-paste"], text=True)
        if tool == "xclip":
            return subprocess.check_output(["xclip", "-selection", "clipboard", "-o"], text=True)
        if tool == "xsel":
            return subprocess.check_output(["xsel", "--clipboard", "--output"], text=True)
        return None

    def write_clipboard(self, text: str):
        tool = self._find_clipboard_tool()
        if not tool:
            raise DesktopBackendError("No clipboard tool found")
        
        if tool == "wl-copy":
            p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode())
        elif tool == "xclip":
            p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode())
        elif tool == "xsel":
            p = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode())

    def get_selected_text(self) -> Optional[str]:
        return None

    def get_active_window(self) -> Dict[str, Any]:
        return {}

    def screenshot(self) -> Optional[bytes]:
        return None

    def show_overlay(self, message: str):
        self.notify("GhostType", message)

    def notify(self, title: str, message: str):
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message])
        else:
            print(f"[{title}] {message}")
