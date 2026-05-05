class GhostTypeError(Exception):
    """Base class for all GhostType exceptions."""
    pass

class ConfigError(GhostTypeError):
    """Raised when there is an issue with configuration."""
    pass

class DependencyMissing(GhostTypeError):
    """Raised when an external dependency (tool or package) is missing."""
    pass

class CapabilityUnavailable(GhostTypeError):
    """Raised when a requested capability is not supported by the current backend."""
    pass

class ProviderUnavailable(GhostTypeError):
    """Raised when a registered provider is not available on the system."""
    pass

class ProviderNotConfigured(GhostTypeError):
    """Raised when a provider is selected but lacks necessary configuration (e.g., API keys)."""
    pass

class PolicyDenied(GhostTypeError):
    """Raised when an action or context capture is denied by the privacy/safety policy."""
    pass

class RouterError(GhostTypeError):
    """Raised when the router fails to process a request."""
    pass

class InvalidRouterOutput(RouterError):
    """Raised when the router returns an invalid or schema-non-compliant response."""
    pass

class ActionExecutionError(GhostTypeError):
    """Raised when an action fails during execution."""
    pass

class DesktopBackendError(GhostTypeError):
    """Raised when a desktop backend operation fails."""
    pass

class STTError(GhostTypeError):
    """Raised when speech-to-text transcription fails."""
    pass

class LLMError(GhostTypeError):
    """Raised when an LLM provider fails to return a response."""
    pass

class ContextError(GhostTypeError):
    """Raised when context collection fails."""
    pass
