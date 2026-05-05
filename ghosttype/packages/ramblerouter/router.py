import json
import re
from typing import Dict, Any, List, Optional
from ghosttype.core.errors import RouterError, InvalidRouterOutput


class Router:
    """Routes text to appropriate actions."""
    
    def __init__(self, fast_llm: str = "groq", fast_model: str = "llama-3.1-8b-instant"):
        self.fast_llm = fast_llm
        self.fast_model = fast_model
        self._deterministic_parser = DeterministicParser()
    
    def route(self, text: str) -> Dict[str, Any]:
        """Route text to actions."""
        # Try deterministic parser first
        result = self._deterministic_parser.parse(text)
        
        if result:
            return {
                "actions": result,
                "route": "deterministic",
                "confidence": 1.0,
            }
        
        # Fall back to LLM routing
        return self._route_with_llm(text)
    
    def _route_with_llm(self, text: str) -> Dict[str, Any]:
        """Route text using LLM."""
        # For now, return a simple dictation action
        return {
            "actions": [
                {
                    "type": "insert_text",
                    "text": text,
                }
            ],
            "route": "dictation",
            "confidence": 0.5,
        }


class DeterministicParser:
    """Deterministic parser for common voice commands."""
    
    def __init__(self):
        self._patterns = self._build_patterns()
    
    def _build_patterns(self) -> List[Dict[str, Any]]:
        """Build parsing patterns."""
        return [
            {
                "name": "new_line",
                "pattern": r"\bnew\s+line\b",
                "action": {"type": "press_key", "key": "Enter"},
            },
            {
                "name": "tab",
                "pattern": r"\btab\b",
                "action": {"type": "press_key", "key": "Tab"},
            },
            {
                "name": "backspace",
                "pattern": r"\bbackspace\b",
                "action": {"type": "press_key", "key": "BackSpace"},
            },
            {
                "name": "scrap_that",
                "pattern": r"\b(scrap|scratch|undo)\s+that\b",
                "action": {"type": "undo_last_chunk"},
            },
            {
                "name": "delete_last_word",
                "pattern": r"\bdelete\s+last\s+word\b",
                "action": {"type": "delete_last_word"},
            },
        ]
    
    def parse(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """Parse text into actions."""
        actions = []
        remaining_text = text
        
        # Check for patterns
        for pattern in self._patterns:
            match = re.search(pattern["pattern"], remaining_text, re.IGNORECASE)
            if match:
                # Add any text before the match
                before = remaining_text[:match.start()].strip()
                if before:
                    actions.append({"type": "insert_text", "text": before})
                
                # Add the action
                actions.append(pattern["action"])
                
                # Continue with remaining text
                remaining_text = remaining_text[match.end():].strip()
        
        # Add any remaining text
        if remaining_text:
            actions.append({"type": "insert_text", "text": remaining_text})
        
        # If we found any patterns, return actions
        if len(actions) > 1 or (len(actions) == 1 and actions[0]["type"] != "insert_text"):
            return actions
        
        return None
