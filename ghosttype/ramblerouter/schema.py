"""Schema definitions for router."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RouteType(Enum):
    """Available route types."""
    DICTATION = "dictation"
    LOCAL = "local"
    FAST_LLM = "fast_llm"
    STRONG_LLM = "strong_llm"
    ESCALATION_LLM = "escalation_llm"
    PRIVATE_LLM = "private_llm"
    AGENT = "agent"


@dataclass
class ActionSchema:
    """Schema for an action."""
    type: str
    text: Optional[str] = None
    key: Optional[str] = None
    message: Optional[str] = None
    route: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type}
        if self.text is not None:
            result["text"] = self.text
        if self.key is not None:
            result["key"] = self.key
        if self.message is not None:
            result["message"] = self.message
        if self.route is not None:
            result["route"] = self.route
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionSchema":
        return cls(
            type=data.get("type", ""),
            text=data.get("text"),
            key=data.get("key"),
            message=data.get("message"),
            route=data.get("route"),
        )


@dataclass
class RouteSchema:
    """Schema for a route."""
    name: str
    type: RouteType
    description: str
    requires_llm: bool = False
    requires_context: bool = False
    supports_streaming: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "requires_llm": self.requires_llm,
            "requires_context": self.requires_context,
            "supports_streaming": self.supports_streaming,
        }


@dataclass
class RouterSchema:
    """Schema for the router."""
    version: str = "1.0"
    routes: List[RouteSchema] = None
    actions: List[ActionSchema] = None
    
    def __post_init__(self):
        if self.routes is None:
            self.routes = self._default_routes()
        if self.actions is None:
            self.actions = self._default_actions()
    
    def _default_routes(self) -> List[RouteSchema]:
        """Get default routes."""
        return [
            RouteSchema(
                name="dictation",
                type=RouteType.DICTATION,
                description="Simple text insertion",
                requires_llm=False,
                requires_context=False,
            ),
            RouteSchema(
                name="local",
                type=RouteType.LOCAL,
                description="Local commands (new line, tab, scrap that)",
                requires_llm=False,
                requires_context=False,
            ),
            RouteSchema(
                name="fast_llm",
                type=RouteType.FAST_LLM,
                description="Quick LLM operations",
                requires_llm=True,
                requires_context=False,
            ),
            RouteSchema(
                name="strong_llm",
                type=RouteType.STRONG_LLM,
                description="Complex LLM operations",
                requires_llm=True,
                requires_context=True,
            ),
            RouteSchema(
                name="escalation_llm",
                type=RouteType.ESCALATION_LLM,
                description="Escalation LLM operations",
                requires_llm=True,
                requires_context=True,
            ),
            RouteSchema(
                name="private_llm",
                type=RouteType.PRIVATE_LLM,
                description="Private LLM operations",
                requires_llm=True,
                requires_context=False,
            ),
            RouteSchema(
                name="agent",
                type=RouteType.AGENT,
                description="Agent operations",
                requires_llm=True,
                requires_context=True,
            ),
        ]
    
    def _default_actions(self) -> List[ActionSchema]:
        """Get default actions."""
        return [
            ActionSchema(type="insert_text", description="Insert text"),
            ActionSchema(type="replace_selection", description="Replace selected text"),
            ActionSchema(type="copy_to_clipboard", description="Copy to clipboard"),
            ActionSchema(type="paste_text", description="Paste text"),
            ActionSchema(type="type_text", description="Type text"),
            ActionSchema(type="press_key", description="Press a key"),
            ActionSchema(type="undo_last_chunk", description="Undo last chunk"),
            ActionSchema(type="delete_last_word", description="Delete last word"),
            ActionSchema(type="show_overlay", description="Show overlay"),
            ActionSchema(type="ask_confirmation", description="Ask for confirmation"),
            ActionSchema(type="route_to_strong_llm", description="Route to strong LLM"),
            ActionSchema(type="route_to_agent", description="Route to agent"),
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "routes": [r.to_dict() for r in self.routes],
            "actions": [a.to_dict() for a in self.actions],
        }
