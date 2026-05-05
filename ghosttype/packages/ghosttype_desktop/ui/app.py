import sys
from typing import Optional, Dict, Any
import asyncio
import threading

from gi.repository import Gtk, Gdk, Adw, GLib, Gio


@Gtk.Template(filename='/org/ghosttype/app.ui')
class GhostTypeWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'GhostTypeWindow'
    
    status_label = Gtk.Template.Child()
    transcript_view = Gtk.Template.Child()
    status_page = Gtk.Template.Child()
    start_button = Gtk.Template.Child()
    stop_button = Gtk.Template.Child()
    settings_button = Gtk.Template.Child()
    
    def __init__(self, app: Adw.Application, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._state = "idle"
        self._transcript_buffer = self.transcript_view.get_buffer()
        
        self.start_button.connect("clicked", self._on_start)
        self.stop_button.connect("clicked", self._on_stop)
        self.settings_button.connect("clicked", self._on_settings)
        
        self._update_state("idle")
    
    def _on_start(self, button):
        self._update_state("recording")
        if hasattr(self.app, 'ghosttype_app'):
            self.app.ghosttype_app.start_recording()
    
    def _on_stop(self, button):
        self._update_state("processing")
        if hasattr(self.app, 'ghosttype_app'):
            self.app.ghosttype_app.stop_recording()
    
    def _on_settings(self, button):
        pass
    
    def _update_state(self, state: str):
        self._state = state
        
        if state == "idle":
            self.status_label.set_text("Ready")
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.status_page.set_icon_name("audio-input-microphone")
        elif state == "recording":
            self.status_label.set_text("Recording...")
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.status_page.set_icon_name("audio-input-microphone-high")
        elif state == "processing":
            self.status_label.set_text("Processing...")
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
            self.status_page.set_icon_name("emblem-synchronizing")
        elif state == "error":
            self.status_label.set_text("Error")
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.status_page.set_icon_name("dialog-error")
    
    def add_transcript(self, text: str):
        end_iter = self._transcript_buffer.get_end_iter()
        self._transcript_buffer.insert(end_iter, text + "\n")
        
        mark = self._transcript_buffer.create_mark("end", end_iter, False)
        self.transcript_view.scroll_mark_onscreen(mark)
    
    def set_status(self, message: str):
        GLib.idle_add(self.status_label.set_text, message)


class GhostTypeApplication(Adw.Application):
    __gtype_name__ = 'GhostTypeApplication'
    
    window: Optional[GhostTypeWindow] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)
        
        self.ghosttype_app = None
    
    def on_activate(self, app):
        if self.window is None:
            self.window = GhostTypeWindow(application=app)
        
        self.window.present()
    
    def set_ghosttype_app(self, gt_app):
        self.ghosttype_app = gt_app


class GhostTypeUI:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._app: Optional[GhostTypeApplication] = None
        self._window: Optional[GhostTypeWindow] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
    
    def _run_gtk(self):
        self._app = GhostTypeApplication()
        self._window = self._app.window
        
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


def launch_ui(config: Optional[Dict[str, Any]] = None) -> GhostTypeUI:
    return GhostTypeUI(config)
