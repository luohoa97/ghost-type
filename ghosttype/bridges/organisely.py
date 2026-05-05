from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging
import httpx

from ghosttype.core.config import GhostTypeConfig
from ghosttype.core.errors import BridgeError


class OrganiselyConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class OrganiselyTask:
    id: str
    title: str
    completed: bool = False
    priority: str = "normal"
    due_date: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "completed": self.completed,
            "priority": self.priority,
            "due_date": self.due_date,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrganiselyTask":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            completed=data.get("completed", False),
            priority=data.get("priority", "normal"),
            due_date=data.get("due_date"),
            tags=data.get("tags", []),
        )


class OrganiselyBridge:
    def __init__(
        self,
        config: GhostTypeConfig,
        api_key: Optional[str] = None,
        base_url: str = "https://api.organisely.app/v1",
    ):
        self.config = config
        self._api_key = api_key
        self._base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None
        self._status = OrganiselyConnectionStatus.DISCONNECTED
        self._logger = logging.getLogger("ghosttype.bridges.organisely")
    
    def _get_api_key(self) -> Optional[str]:
        if self._api_key:
            return self._api_key
        
        secrets = getattr(self.config, "secrets", {})
        return secrets.get("organisely_api_key")
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            api_key = self._get_api_key()
            
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=30.0,
            )
        
        return self._client
    
    async def connect(self) -> bool:
        try:
            self._status = OrganiselyConnectionStatus.CONNECTING
            client = await self._get_client()
            
            response = await client.get("/health")
            
            if response.status_code == 200:
                self._status = OrganiselyConnectionStatus.CONNECTED
                self._logger.info("Connected to Organisely")
                return True
            else:
                self._status = OrganiselyConnectionStatus.ERROR
                return False
                
        except httpx.HTTPStatusError as e:
            self._status = OrganiselyConnectionStatus.ERROR
            self._logger.error(f"Organisely connection error: {e}")
            return False
        except Exception as e:
            self._status = OrganiselyConnectionStatus.ERROR
            self._logger.error(f"Organisely connection failed: {e}")
            return False
    
    async def disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        self._status = OrganiselyConnectionStatus.DISCONNECTED
    
    async def list_tasks(
        self,
        completed: Optional[bool] = None,
        priority: Optional[str] = None,
        limit: int = 50,
    ) -> List[OrganiselyTask]:
        if self._status != OrganiselyConnectionStatus.CONNECTED:
            if not await self.connect():
                raise BridgeError("Not connected to Organisely")
        
        try:
            client = await self._get_client()
            
            params = {"limit": limit}
            if completed is not None:
                params["completed"] = completed
            if priority:
                params["priority"] = priority
            
            response = await client.get("/tasks", params=params)
            response.raise_for_status()
            
            data = response.json()
            return [OrganiselyTask.from_dict(t) for t in data.get("tasks", [])]
            
        except httpx.HTTPStatusError as e:
            raise BridgeError(f"Failed to list tasks: {e}")
        except Exception as e:
            raise BridgeError(f"Failed to list tasks: {e}")
    
    async def create_task(
        self,
        title: str,
        priority: str = "normal",
        due_date: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> OrganiselyTask:
        if self._status != OrganiselyConnectionStatus.CONNECTED:
            if not await self.connect():
                raise BridgeError("Not connected to Organisely")
        
        try:
            client = await self._get_client()
            
            payload = {
                "title": title,
                "priority": priority,
            }
            if due_date:
                payload["due_date"] = due_date
            if tags:
                payload["tags"] = tags
            
            response = await client.post("/tasks", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return OrganiselyTask.from_dict(data)
            
        except httpx.HTTPStatusError as e:
            raise BridgeError(f"Failed to create task: {e}")
        except Exception as e:
            raise BridgeError(f"Failed to create task: {e}")
    
    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        completed: Optional[bool] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> OrganiselyTask:
        if self._status != OrganiselyConnectionStatus.CONNECTED:
            if not await self.connect():
                raise BridgeError("Not connected to Organisely")
        
        try:
            client = await self._get_client()
            
            payload = {}
            if title is not None:
                payload["title"] = title
            if completed is not None:
                payload["completed"] = completed
            if priority is not None:
                payload["priority"] = priority
            if due_date is not None:
                payload["due_date"] = due_date
            if tags is not None:
                payload["tags"] = tags
            
            response = await client.patch(f"/tasks/{task_id}", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return OrganiselyTask.from_dict(data)
            
        except httpx.HTTPStatusError as e:
            raise BridgeError(f"Failed to update task: {e}")
        except Exception as e:
            raise BridgeError(f"Failed to update task: {e}")
    
    async def complete_task(self, task_id: str) -> OrganiselyTask:
        return await self.update_task(task_id, completed=True)
    
    async def delete_task(self, task_id: str) -> bool:
        if self._status != OrganiselyConnectionStatus.CONNECTED:
            if not await self.connect():
                raise BridgeError("Not connected to Organisely")
        
        try:
            client = await self._get_client()
            response = await client.delete(f"/tasks/{task_id}")
            response.raise_for_status()
            return True
            
        except httpx.HTTPStatusError as e:
            raise BridgeError(f"Failed to delete task: {e}")
        except Exception as e:
            raise BridgeError(f"Failed to delete task: {e}")
    
    def get_status(self) -> OrganiselyConnectionStatus:
        return self._status
    
    def is_connected(self) -> bool:
        return self._status == OrganiselyConnectionStatus.CONNECTED
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "status": self._status.value,
            "base_url": self._base_url,
            "api_key_configured": self._get_api_key() is not None,
        }


async def create_organisely_bridge(config: GhostTypeConfig) -> Optional[OrganiselyBridge]:
    api_key = None
    try:
        secrets = getattr(config, "secrets", {})
        api_key = secrets.get("organisely_api_key")
    except Exception:
        pass
    
    return OrganiselyBridge(config, api_key)
