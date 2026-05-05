"""Local commands parser for GhostType."""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ghosttype.ramblerouter.router import Action, RouterOutput


@dataclass
class CommandPattern:
    """Pattern for a local command."""
    regex: str
    action_type: str
    description: str


class LocalCommandsParser:
    """Parses local voice commands."""
    
    def __init__(self):
        self._patterns = self._create_patterns()
    
    def _create_patterns(self) -> List[CommandPattern]:
        """Create command patterns."""
        return [
            # New line
            CommandPattern(
                regex=r'\bnew\s+line\b',
                action_type="press_key",
                description="Insert a new line",
            ),
            # Tab
            CommandPattern(
                regex=r'\btab\b',
                action_type="press_key",
                key="Tab",
                description="Insert a tab",
            ),
            # Backspace
            CommandPattern(
                regex=r'\bbackspace\b',
                action_type="press_key",
                key="BackSpace",
                description="Press backspace",
            ),
            # Scrap that / Scratch that / Undo that
            CommandPattern(
                regex=r'\b(scrap|scratch|undo)\s+that\b',
                action_type="undo_last_chunk",
                description="Undo last chunk",
            ),
            # Delete last word
            CommandPattern(
                regex=r'\bdelete\s+last\s+word\b',
                action_type="delete_last_word",
                description="Delete last word",
            ),
            # Replace that with
            CommandPattern(
                regex=r'\breplace\s+that\s+with\s+(.+)',
                action_type="replace_selection",
                description="Replace last chunk",
            ),
            # Literal
            CommandPattern(
                regex=r'\bliteral\s+(.+)',
                action_type="insert_text",
                description="Insert text literally",
            ),
            # Press key
            CommandPattern(
                regex=r'\bpress\s+(.+)',
                action_type="press_key",
                description="Press a key",
            ),
        ]
    
    def parse(self, text: str) -> List[Action]:
        """Parse text into actions."""
        actions = []
        remaining_text = text
        
        # Check for patterns
        for pattern in self._patterns:
            match = re.search(pattern.regex, remaining_text, re.IGNORECASE)
            if match:
                action = Action(
                    type=pattern.action_type,
                    text=match.group(1) if len(match.groups()) > 0 else "",
                    key=pattern.key if hasattr(pattern, 'key') else "",
                )
                actions.append(action)
                
                # Remove matched text
                remaining_text = remaining_text[:match.start()] + remaining_text[match.end():]
        
        # If no patterns matched, treat as dictation
        if not actions and remaining_text.strip():
            actions = [Action(type="insert_text", text=remaining_text.strip())]
        
        return actions
    
    def parse_with_route(self, text: str) -> RouterOutput:
        """Parse text and return router output."""
        actions = self.parse(text)
        
        # Determine route
        if any(a.type in ["undo_last_chunk", "delete_last_word", "press_key"] for a in actions):
            route = "local"
        else:
            route = "dictation"
        
        return RouterOutput(
            route=route,
            actions=actions,
            confidence=1.0,
            raw_text=text,
        )
    
    def is_local_command(self, text: str) -> bool:
        """Check if text contains a local command."""
        for pattern in self._patterns:
            if re.search(pattern.regex, text, re.IGNORECASE):
                return True
        return False
    
    def get_commands(self) -> List[Dict[str, str]]:
        """Get list of available commands."""
        return [
            {
                "pattern": p.regex,
                "action": p.action_type,
                "description": p.description,
            }
            for p in self._patterns
        ]
