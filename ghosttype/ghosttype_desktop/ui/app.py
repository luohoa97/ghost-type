import sys
from typing import Optional, Dict, Any
import threading
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gi.repository import Gtk, Gdk, Adw, GLib, Gio

from ghosttype_desktop.app import GhostTypeDesktopApp, create_app


class GhostTypeWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, voice_key: str = "F24", **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._state = "idle"
        self._voice_key = voice_key

        self.set_title("GhostType")
        self.set_default_size(400, 300)

        self._build_ui()

    def _build_ui(self):
        header = Adw.HeaderBar()
        header.set_title("GhostType")
        self.set_titlebar(header)

        clamp = Adw.Clamp()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)

        self.status_label = Gtk.Label()
        self.status_label.set_markup("<big>Ready</big>")
        self.status_label.set_halign(Gtk.Align.CENTER)
        box.append(self.status_label)

        self.status_icon = Gtk.Image.new_from_icon_name("audio-input-microphone")
        self.status_icon.set_pixel_size(64)
        self.status_icon.set_valign(Gtk.Align.CENTER)
        box.append(self.status_icon)

        self.instruction_label = Gtk.Label()
        self.instruction_label.set_markup(f"<small>Press {self._voice_key} to start recording</small>")
        self.instruction_label.set_halign(Gtk.Align.CENTER)
        box.append(self.instruction_label)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.CENTER)

        self.start_button = Gtk.Button.new_with_label("Start")
        self.start_button.set_icon_name("media-record")
        self.start_button.add_css_class("suggested-action")
        self.start_button.connect("clicked", self._on_start)
        button_box.append(self.start_button)

        self.stop_button = Gtk.Button.new_with_label("Stop")
        self.stop_button.set_icon_name("media-playback-stop")
        self.stop_button.set_sensitive(False)
        self.stop_button.connect("clicked", self._on_stop)
        button_box.append(self.stop_button)

        box.append(button_box)

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_vertical(12)
        box.append(separator)

        transcript_label = Gtk.Label()
        transcript_label.set_markup("<b>Transcript</b>")
        transcript_label.set_halign(Gtk.Align.START)
        box.append(transcript_label)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        self.transcript_buffer = Gtk.TextBuffer()
        self.transcript_view = Gtk.TextView.new_with_buffer(self.transcript_buffer)
        self.transcript_view.set_editable(False)
        self.transcript_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scrolled.set_child(self.transcript_view)

        box.append(scrolled)

        clamp.set_child(box)
        clamp.set_maximum_size(500)
        clamp.set_valign(Gtk.Align.CENTER)

        self.set_content(clamp)

    def _on_start(self, button):
        self._update_state("recording")
        if hasattr(self.app, 'ghosttype_app') and self.app.ghosttype_app:
            self.app.ghosttype_app.start_recording()

    def _on_stop(self, button):
        self._update_state("processing")
        if hasattr(self.app, 'ghosttype_app') and self.app.ghosttype_app:
            self.app.ghosttype_app.stop_recording()

    def _update_state(self, state: str):
        self._state = state

        if state == "idle":
            self.status_label.set_markup("<big>Ready</big>")
            self.status_icon.set_from_icon_name("audio-input-microphone")
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
        elif state == "recording":
            self.status_label.set_markup("<big>Recording...</big>")
            self.status_icon.set_from_icon_name("audio-input-microphone-high")
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
        elif state == "processing":
            self.status_label.set_markup("<big>Processing...</big>")
            self.status_icon.set_from_icon_name("emblem-synchronizing")
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
        elif state == "result":
            self.status_label.set_markup("<big>Result</big>")
            self.status_icon.set_from_icon_name("emblem-ok-symbolic")
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
        elif state == "error":
            self.status_label.set_markup("<big>Error</big>")
            self.status_icon.set_from_icon_name("dialog-error")
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)

    def add_transcript(self, text: str):
        end_iter = self.transcript_buffer.get_end_iter()
        self.transcript_buffer.insert(end_iter, text + "\n")

        mark = self.transcript_buffer.create_mark("end", end_iter, False)
        self.transcript_view.scroll_mark_onscreen(mark)

    def set_status(self, message: str):
        self.status_label.set_markup(f"<big>{message}</big>")

    def get_state(self) -> str:
        return self._state


class GhostTypeApplication(Adw.Application):
    def __init__(self, voice_key: str = "F24", **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

        self.ghosttype_app: Optional[GhostTypeDesktopApp] = None
        self.window: Optional[GhostTypeWindow] = None
        self._voice_key = voice_key

    def _setup_ghosttype_app(self):
        """Setup the main GhostType app."""
        self.ghosttype_app = create_app()

        def on_transcript(transcript: str):
            if self.window:
                GLib.idle_add(self.window.add_transcript, transcript)

        def on_event(event_type: str, data=None):
            if event_type == "recording_started" and self.window:
                GLib.idle_add(self.window._update_state, "recording")
            elif event_type == "recording_stopped" and self.window:
                GLib.idle_add(self.window._update_state, "processing")
            elif event_type == "transcription_complete" and self.window:
                GLib.idle_add(self.window._update_state, "result")
            elif event_type == "error" and self.window:
                GLib.idle_add(self.window._update_state, "error")

        self.ghosttype_app.set_transcript_callback(on_transcript)
        self.ghosttype_app.set_event_callback(on_event)

        try:
            self.ghosttype_app.start_hotkey_listening()
        except Exception as e:
            print(f"Warning: Could not start hotkey listening: {e}")

    def on_activate(self, app):
        if self.window is None:
            self.window = GhostTypeWindow(application=app, voice_key=self._voice_key)

        if self.ghosttype_app is None:
            self._setup_ghosttype_app()

        self.window.present()


class GhostTypeUI:
    def __init__(self, config: Optional[Dict[str, Any]] = None, voice_key: str = "F24"):
        self.config = config or {}
        self._app: Optional[GhostTypeApplication] = None
        self._window: Optional[GhostTypeWindow] = None
        self._thread: Optional[threading.Thread] = None
        self._voice_key = voice_key

    def _run_gtk(self):
        self._app = GhostTypeApplication(voice_key=self._voice_key)
        self._window = self._app.window
        self._app._setup_ghosttype_app()
        self._app.run(None)

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._run_gtk, daemon=True)
        self._thread.start()

        import time
        time.sleep(0.5)

    def stop(self):
        if self._app:
            self._app.quit()

    def set_status(self, message: str):
        if self._window:
            GLib.idle_add(self._window.set_status, message)

    def add_transcript(self, text: str):
        if self._window:
            GLib.idle_add(self._window.add_transcript, text)

    def update_state(self, state: str):
        if self._window:
            GLib.idle_add(self._window._update_state, state)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def get_state(self) -> str:
        if self._window:
            return self._window.get_state()
        return "idle"


def launch_ui(config: Optional[Dict[str, Any]] = None, voice_key: Optional[str] = None) -> GhostTypeUI:
    if voice_key is None:
        from ghosttype.core.config import ConfigManager
        config_manager = ConfigManager()
        config_manager.load()
        voice_key = config_manager.config.hotkeys.voice_key
    return GhostTypeUI(config, voice_key=voice_key)


def main():
    app = GhostTypeApplication()
    app._setup_ghosttype_app()
    app.run(None)


if __name__ == "__main__":
    main()
