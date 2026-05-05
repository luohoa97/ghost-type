import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import tomlkit
from pydantic import BaseModel, Field
from platformdirs import PlatformDirs
from .errors import ConfigError

class AppConfig(BaseModel):
    mode: str = "fast"
    show_overlay: bool = True
    play_sounds: bool = True
    history_mode: str = "session"

class FeatureConfig(BaseModel):
    stt: bool = True
    smart_router: bool = True
    llm_cleanup: bool = True
    routing: bool = True
    prefixes: bool = True
    assistant_modes: bool = True
    ocr: bool = False
    history: bool = True
    streaming: bool = False
    organisely_bridge: bool = False

class HotkeyConfig(BaseModel):
    backend: str = "keyd"
    voice_key: str = "F24"
    record_mode: str = "hold"
    cancel_key: str = "Escape"
    ocr_key: str = "Shift+F24"

class DesktopConfig(BaseModel):
    backend: str = "auto"
    fallback_backend: str = "generic"
    output_method: str = "clipboard_paste"
    prefer_native_bridge: bool = True

class STTConfig(BaseModel):
    provider: str = "insanely_fast_whisper"
    model: str = "openai/whisper-large-v3"
    language: str = "auto"
    fallback_provider: str = "groq"
    fallback_model: str = "whisper-large-v3-turbo"

class SecretConfig(BaseModel):
    groq_api_key: str = "env:GROQ_API_KEY"
    openrouter_api_key: str = "env:OPENROUTER_API_KEY"

class GhostTypeConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    hotkeys: HotkeyConfig = Field(default_factory=HotkeyConfig)
    desktop: DesktopConfig = Field(default_factory=DesktopConfig)
    stt: STTConfig = Field(default_factory=STTConfig)
    secrets: SecretConfig = Field(default_factory=SecretConfig)

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.dirs = PlatformDirs("ghosttype", "ghosttype")
        self.config_dir = Path(self.dirs.user_config_dir)
        self.config_path = Path(config_path) if config_path else self.config_dir / "config.toml"
        self._config: Optional[GhostTypeConfig] = None
        self._raw_data: tomlkit.TOMLDocument = tomlkit.document()

    def ensure_dirs(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        Path(self.dirs.user_data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.dirs.user_cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.dirs.user_state_dir).mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.config_path.exists():
            self._config = GhostTypeConfig()
            return

        try:
            with open(self.config_path, "r") as f:
                self._raw_data = tomlkit.load(f)
                self._config = GhostTypeConfig.model_validate(self._raw_data)
        except Exception as e:
            raise ConfigError(f"Failed to load config from {self.config_path}: {e}")

    @property
    def config(self) -> GhostTypeConfig:
        if self._config is None:
            self.load()
        return self._config

    def get_redacted_config(self) -> Dict[str, Any]:
        data = self.config.model_dump()
        if "secrets" in data:
            for key in data["secrets"]:
                val = data["secrets"][key]
                if val.startswith("env:"):
                    env_key = val.split(":", 1)[1]
                    if env_key in os.environ:
                        data["secrets"][key] = f"env:{env_key} (SET)"
                    else:
                        data["secrets"][key] = f"env:{env_key} (MISSING)"
                else:
                    data["secrets"][key] = "********"
        return data

    def init_default(self):
        self.ensure_dirs()
        if self.config_path.exists():
            return
        default_config = GhostTypeConfig()
        # Create a document from the default model
        doc = tomlkit.document()
        for section, subconfig in default_config.model_dump().items():
            doc[section] = subconfig
        with open(self.config_path, "w") as f:
            tomlkit.dump(doc, f)

    def get_path(self, name: str) -> Path:
        if name == "config": return self.config_path
        if name == "data": return Path(self.dirs.user_data_dir)
        if name == "cache": return Path(self.dirs.user_cache_dir)
        if name == "state": return Path(self.dirs.user_state_dir)
        raise ConfigError(f"Unknown path type: {name}")

    def get_dotted(self, key: str) -> Any:
        parts = key.split(".")
        val = self.config.model_dump()
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                raise ConfigError(f"Key {key} not found")
        return val

    def set_dotted(self, key: str, value: Any):
        # Update raw data to preserve formatting if possible, though pydantic/tomlkit mixing is tricky
        parts = key.split(".")
        curr = self._raw_data
        for p in parts[:-1]:
            if p not in curr:
                curr[p] = tomlkit.table()
            curr = curr[p]
        
        # Simple type conversion for value
        if value.lower() == "true": value = True
        elif value.lower() == "false": value = False
        elif value.isdigit(): value = int(value)
        
        curr[parts[-1]] = value
        
        with open(self.config_path, "w") as f:
            tomlkit.dump(self._raw_data, f)
        self.load() # Reload
