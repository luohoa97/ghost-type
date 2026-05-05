from typing import Dict, List, Type, Any, Optional
from abc import ABC, abstractmethod

class Provider(ABC):
    @property
    @abstractmethod
    def id(self) -> str: pass

    @property
    @abstractmethod
    def name(self) -> str: pass

    @property
    @abstractmethod
    def provider_type(self) -> str: pass

    @abstractmethod
    def is_available(self) -> bool: pass

    @abstractmethod
    def diagnostics(self) -> Dict[str, Any]: pass

    @property
    @abstractmethod
    def required_dependencies(self) -> List[str]: pass

class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, Provider] = {}

    def register(self, provider: Provider):
        self._providers[provider.id] = provider

    def get(self, provider_id: str) -> Optional[Provider]:
        return self._providers.get(provider_id)

    def list_by_type(self, provider_type: str) -> List[Provider]:
        return [p for p in self._providers.values() if p.provider_type == provider_type]

    def list_all(self) -> List[Provider]:
        return list(self._providers.values())
