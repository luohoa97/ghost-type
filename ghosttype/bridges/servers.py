from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
import uuid

import httpx

from ghosttype.core.config import GhostTypeConfig


class BridgeServerState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


@dataclass
class BridgeRequest:
    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]] = None
    query_params: Dict[str, str] = None
    
    def __post_init__(self):
        if self.query_params is None:
            self.query_params = {}


@dataclass
class BridgeResponse:
    status: int
    body: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class HTTPRoute:
    def __init__(
        self,
        path: str,
        method: str = "GET",
        handler: Optional[Callable[[BridgeRequest], Awaitable[BridgeResponse]]] = None,
    ):
        self.path = path
        self.method = method.upper()
        self.handler = handler


class HTTPBridgeServer:
    def __init__(
        self,
        config: GhostTypeConfig,
        host: str = "127.0.0.1",
        port: int = 8765,
    ):
        self.config = config
        self.host = host
        self.port = port
        self._state = BridgeServerState.STOPPED
        self._server: Optional[asyncio.Server] = None
        self._routes: Dict[str, Dict[str, Callable]] = {}
        self._logger = logging.getLogger("ghosttype.bridges.http")
        
        self._register_default_routes()
    
    def _register_default_routes(self):
        self.add_route("GET", "/health", self._handle_health)
        self.add_route("GET", "/status", self._handle_status)
        self.add_route("POST", "/transcribe", self._handle_transcribe)
        self.add_route("POST", "/route", self._handle_route)
        self.add_route("POST", "/execute", self._handle_execute)
    
    def add_route(
        self,
        method: str,
        path: str,
        handler: Callable[[BridgeRequest], Awaitable[BridgeResponse]],
    ):
        method = method.upper()
        if method not in self._routes:
            self._routes[method] = {}
        self._routes[method][path] = handler
    
    async def _handle_health(self, request: BridgeRequest) -> BridgeResponse:
        return BridgeResponse(
            status=200,
            body={"status": "healthy", "service": "ghosttype"},
        )
    
    async def _handle_status(self, request: BridgeRequest) -> BridgeResponse:
        return BridgeResponse(
            status=200,
            body={"state": self._state.value, "host": self.host, "port": self.port},
        )
    
    async def _handle_transcribe(self, request: BridgeRequest) -> BridgeResponse:
        return BridgeResponse(
            status=200,
            body={"message": "Transcribe endpoint - integrate with STT providers"},
        )
    
    async def _handle_route(self, request: BridgeRequest) -> BridgeResponse:
        text = request.body.get("text", "") if request.body else ""
        return BridgeResponse(
            status=200,
            body={"message": "Route endpoint - integrate with router", "text": text},
        )
    
    async def _handle_execute(self, request: BridgeRequest) -> BridgeResponse:
        return BridgeResponse(
            status=200,
            body={"message": "Execute endpoint - integrate with action executor"},
        )
    
    async def _handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        try:
            request_line = await reader.readline()
            if not request_line:
                return
            
            request_line = request_line.decode().strip()
            parts = request_line.split()
            
            if len(parts) < 2:
                return
            
            method, path = parts[0], parts[1]
            
            headers = {}
            content_length = 0
            
            while True:
                line = await reader.readline()
                if not line or line == b"\r\n":
                    break
                
                header_line = line.decode().strip()
                if ":" in header_line:
                    key, value = header_line.split(":", 1)
                    headers[key.strip()] = value.strip()
                
                if key.lower() == "content-length":
                    content_length = int(value.strip())
            
            body = None
            if content_length > 0:
                body_data = await reader.readexact(content_length)
                try:
                    import json
                    body = json.loads(body_data)
                except json.JSONDecodeError:
                    pass
            
            request = BridgeRequest(
                method=method,
                path=path,
                headers=headers,
                body=body,
            )
            
            handler = self._routes.get(method, {}).get(path)
            
            if handler:
                response = await handler(request)
            else:
                response = BridgeResponse(
                    status=404,
                    body={"error": "Not found"},
                )
            
            import json
            response_body = json.dumps(response.body or {})
            response_headers = {**response.headers, "Content-Length": str(len(response_body))}
            
            response_line = f"HTTP/1.1 {response.status} OK\r\n"
            for key, value in response_headers.items():
                response_line += f"{key}: {value}\r\n"
            response_line += "\r\n"
            
            writer.write(response_line.encode())
            writer.write(response_body.encode())
            await writer.drain()
            
        except Exception as e:
            self._logger.error(f"Error handling request: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def start(self):
        self._state = BridgeServerState.STARTING
        self._logger.info(f"Starting HTTP bridge on {self.host}:{self.port}")
        
        self._server = await asyncio.start_server(
            self._handle_request,
            self.host,
            self.port,
        )
        
        self._state = BridgeServerState.RUNNING
        self._logger.info("HTTP bridge started")
    
    async def stop(self):
        self._state = BridgeServerState.STOPPING
        self._logger.info("Stopping HTTP bridge")
        
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        self._state = BridgeServerState.STOPPED
        self._logger.info("HTTP bridge stopped")
    
    def get_state(self) -> BridgeServerState:
        return self._state
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "host": self.host,
            "port": self.port,
            "routes": [f"{m} {p}" for m, routes in self._routes.items() for p in routes.keys()],
        }


class WebSocketBridgeServer:
    def __init__(
        self,
        config: GhostTypeConfig,
        host: str = "127.0.0.1",
        port: int = 8766,
    ):
        self.config = config
        self.host = host
        self.port = port
        self._state = BridgeServerState.STOPPED
        self._server = None
        self._clients: set = set()
        self._message_handlers: List[Callable] = []
        self._logger = logging.getLogger("ghosttype.bridges.websocket")
    
    async def start(self):
        self._state = BridgeServerState.STARTING
        self._logger.info(f"Starting WebSocket bridge on {self.host}:{self.port}")
        
        try:
            import websockets
            async with websockets.serve(self._handle_client, self.host, self.port):
                self._state = BridgeServerState.RUNNING
                self._logger.info("WebSocket bridge started")
                await asyncio.Future()
        except ImportError:
            self._logger.error("websockets library not installed")
            self._state = BridgeServerState.STOPPED
        except Exception as e:
            self._logger.error(f"Failed to start WebSocket bridge: {e}")
            self._state = BridgeServerState.STOPPED
    
    async def _handle_client(self, websocket, path):
        self._clients.add(websocket)
        self._logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                for handler in self._message_handlers:
                    try:
                        await handler(websocket, message)
                    except Exception as e:
                        self._logger.error(f"Error in message handler: {e}")
                        
                await websocket.send(f"Echo: {message}")
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.remove(websocket)
            self._logger.info(f"Client disconnected: {websocket.remote_address}")
    
    def on_message(self, handler: Callable):
        self._message_handlers.append(handler)
    
    async def broadcast(self, message: str):
        if self._clients:
            await asyncio.gather(
                *[client.send(message) for client in self._clients],
                return_exceptions=True,
            )
    
    async def stop(self):
        self._state = BridgeServerState.STOPPING
        
        for client in self._clients:
            await client.close()
        
        self._state = BridgeServerState.STOPPED
        self._logger.info("WebSocket bridge stopped")
    
    def get_state(self) -> BridgeServerState:
        return self._state
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "host": self.host,
            "port": self.port,
            "connected_clients": len(self._clients),
        }


class MCPBridgeServer:
    def __init__(
        self,
        config: GhostTypeConfig,
    ):
        self.config = config
        self._state = BridgeServerState.STOPPED
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger("ghosttype.bridges.mcp")
        
        self._register_default_tools()
    
    def _register_default_tools(self):
        self.register_tool(
            name="transcribe",
            description="Transcribe audio to text",
            input_schema={
                "type": "object",
                "properties": {
                    "audio_data": {"type": "string", "description": "Base64 encoded audio"},
                },
            },
        )
        
        self.register_tool(
            name="route",
            description="Route text to appropriate action",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to route"},
                },
            },
        )
        
        self.register_tool(
            name="execute",
            description="Execute an action",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action type"},
                    "params": {"type": "object", "description": "Action parameters"},
                },
            },
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
    ):
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
        }
    
    async def start(self):
        self._state = BridgeServerState.STARTING
        self._logger.info("Starting MCP bridge")
        
        try:
            import mcp
            self._state = BridgeServerState.RUNNING
            self._logger.info("MCP bridge started")
        except ImportError:
            self._logger.error("mcp library not installed")
            self._state = BridgeServerState.STOPPED
    
    async def stop(self):
        self._state = BridgeServerState.STOPPING
        self._logger.info("MCP bridge stopped")
        self._state = BridgeServerState.STOPPED
    
    def get_state(self) -> BridgeServerState:
        return self._state
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return list(self._tools.values())
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "tools_count": len(self._tools),
            "tools": list(self._tools.keys()),
        }


async def create_http_bridge(config: GhostTypeConfig) -> HTTPBridgeServer:
    return HTTPBridgeServer(config)


async def create_websocket_bridge(config: GhostTypeConfig) -> WebSocketBridgeServer:
    return WebSocketBridgeServer(config)


async def create_mcp_bridge(config: GhostTypeConfig) -> MCPBridgeServer:
    return MCPBridgeServer(config)
