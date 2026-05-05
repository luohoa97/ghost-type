from ghosttype.core.config import ConfigManager
from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
from ghosttype.packages.ramblerouter.router import Router
from ghosttype.packages.ghosttype_desktop.output.injector import ActionExecutor


class GhostTypeApp:
    def __init__(self):
        self.config = ConfigManager()
        self.config.load()
        self.backend = DesktopRegistry.detect_best_backend()
        self.router = Router("groq", "llama-3.1-8b-instant")
        self.executor = ActionExecutor(self.backend)

    def process_audio(self, audio_data: bytes):
        # 1. Transcribe (Phase 1/2)
        # STT implementation will be added in Phase 2
        from ghosttype.providers.stt.base import STTProvider
        from ghosttype.providers.stt.groq_whisper import GroqWhisperProvider
        
        try:
            provider = GroqWhisperProvider(self.config.config)
            transcript = provider.transcribe(audio_data)
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")
        
        # 2. Route (Phase 3)
        decision = self.router.route(transcript)
        
        # 3. Execute (Phase 3)
        self.executor.execute_sequence(decision["actions"])


if __name__ == "__main__":
    app = GhostTypeApp()
    print(f"GhostType started with backend: {app.backend.get_name()}")
