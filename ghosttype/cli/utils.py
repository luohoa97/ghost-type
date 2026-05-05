from ghosttype.core.config import ConfigManager

_config_manager = None

def get_config_manager():
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
