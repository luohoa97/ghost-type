"""Router module for GhostType."""
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import re

from ghosttype.core.errors import RouterError, InvalidRouterOutput
from ghosttype.providers.llm.base import LLMProvider


class Route(Enum):
    """Available routing options."""
    DICTATION = "dictation"
    FAST_LLM = "fast_llm"
    STRONG_LLM = "strong_llm"
    ESCALATION_LLM = "escalation_llm"
    PRIVATE_LLM = "private_llm"
    AGENT = "agent"
    LOCAL = "local"


@dataclass
class Action:
    """Represents an action to execute."""
    type: str
    text: str = ""
    key: str = ""
    message: str = ""
    route: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type}
        if self.text:
            result["text"] = self.text
        if self.key:
            result["key"] = self.key
        if self.message:
            result["message"] = self.message
        if self.route:
            result["route"] = self.route
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        return cls(
            type=data.get("type", ""),
            text=data.get("text", ""),
            key=data.get("key", ""),
            message=data.get("message", ""),
            route=data.get("route"),
        )


@dataclass
class RouterOutput:
    """Output from the router."""
    route: Route
    actions: List[Action] = field(default_factory=list)
    confidence: float = 1.0
    raw_text: str = ""
    context_required: bool = False
    output_action: Optional[str] = None
    safety_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route.value,
            "actions": [a.to_dict() for a in self.actions],
            "confidence": self.confidence,
            "raw_text": self.raw_text,
            "context_required": self.context_required,
            "output_action": self.output_action,
            "safety_metadata": self.safety_metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RouterOutput":
        return cls(
            route=Route(data.get("route", "dictation")),
            actions=[Action.from_dict(a) for a in data.get("actions", [])],
            confidence=data.get("confidence", 1.0),
            raw_text=data.get("raw_text", ""),
            context_required=data.get("context_required", False),
            output_action=data.get("output_action"),
            safety_metadata=data.get("safety_metadata", {}),
        )


class Router:
    """Routes transcribed text to appropriate actions."""
    
    def __init__(
        self,
        fast_llm: Optional[LLMProvider] = None,
        strong_llm: Optional[LLMProvider] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.fast_llm = fast_llm
        self.strong_llm = strong_llm
        self.config = config or {}
        
        # Load config sections
        self.features_config = self.config.get("features", {})
        self.routing_config = self.config.get("routing", {})
        self.prefixes_config = self.config.get("prefixes", {})
        
        # Initialize local commands parser
        self._local_commands = None
    
    def _get_local_commands(self):
        """Get or create local commands parser."""
        if self._local_commands is None:
            from .local_commands import LocalCommandsParser
            self._local_commands = LocalCommandsParser()
        return self._local_commands
    
    def route(self, text: str) -> RouterOutput:
        """Route text to appropriate action."""
        # Check if smart router is enabled
        if not self.features_config.get("smart_router", True):
            # Bypass routing, return dictation
            return RouterOutput(
                route=Route.DICTATION,
                actions=[Action(type="insert_text", text=text)],
                raw_text=text,
            )
        
        # Try fast LLM first if available
        if self.fast_llm and self.fast_llm.is_available():
            try:
                return self._route_with_llm(text, self.fast_llm)
            except Exception:
                pass
        
        # Fall back to deterministic parser
        return self._route_deterministic(text)
    
    def _route_with_llm(self, text: str, llm: LLMProvider) -> RouterOutput:
        """Route text using LLM."""
        try:
            # Build prompt
            prompt = self._build_routing_prompt(text)
            
            # Make request
            response = llm.complete({
                "messages": [{"role": "user", "content": prompt}],
                "response_format": "json",
            })
            
            # Parse response
            content = response.get("content", "")
            data = self._parse_router_output(content)
            
            return RouterOutput(
                route=Route(data.get("route", "dictation")),
                actions=[Action.from_dict(a) for a in data.get("actions", [])],
                confidence=data.get("confidence", 0.5),
                raw_text=text,
                context_required=data.get("context_required", False),
                output_action=data.get("output_action"),
                safety_metadata=data.get("safety_metadata", {}),
            )
            
        except Exception as e:
            raise RouterError(f"Failed to route with LLM: {e}")
    
    def _route_deterministic(self, text: str) -> RouterOutput:
        """Route text using deterministic parsing."""
        parser = self._get_local_commands()
        actions = parser.parse(text)
        
        if actions:
            return RouterOutput(
                route=Route.LOCAL,
                actions=actions,
                confidence=1.0,
                raw_text=text,
            )
        
        # Default to dictation
        return RouterOutput(
            route=Route.DICTATION,
            actions=[Action(type="insert_text", text=text)],
            raw_text=text,
        )
    
    def _build_routing_prompt(self, text: str) -> str:
        """Build routing prompt."""
        return f"""You are a voice command router. Your task is to analyze the following transcribed text and determine the appropriate action.

Available routes:
- dictation: Simple text insertion
- local: Local commands like "new line", "tab", "scrap that"
- fast_llm: Quick LLM operations
- strong_llm: Complex LLM operations
- private_llm: Private LLM operations

Return a JSON object with:
- route: The selected route
- actions: Array of actions to execute
- confidence: Your confidence level (0-1)
- context_required: Whether context is needed
- output_action: Optional output action
- safety_metadata: Any safety considerations

Transcribed text: "{text}"

Return ONLY valid JSON."""
    
    def _parse_router_output(self, content: str) -> Dict[str, Any]:
        """Parse router output from LLM."""
        # Try to extract JSON from response
        try:
            # Try direct JSON parse
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return data
            except json.JSONDecodeError:
                pass
        
        raise InvalidRouterOutput(f"Could not parse router output: {content}")
    
    def diagnostics(self) -> Dict[str, Any]:
        """Get router diagnostics."""
        return {
            "fast_llm_available": self.fast_llm.is_available() if self.fast_llm else False,
            "strong_llm_available": self.strong_llm.is_available() if self.strong_llm else False,
            "smart_router_enabled": self.features_config.get("smart_router", True),
            "local_commands_available": True,
        }
