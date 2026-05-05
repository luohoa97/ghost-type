from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Action(BaseModel):
    """Represents a single action."""
    type: str = Field(..., description="Action type")
    text: Optional[str] = Field(None, description="Text to insert")
    key: Optional[str] = Field(None, description="Key to press")
    message: Optional[str] = Field(None, description="Message for overlay/confirmation")


class ActionSequence(BaseModel):
    """Represents a sequence of actions."""
    actions: List[Action] = Field(..., description="List of actions")
    route: Optional[str] = Field(None, description="Route taken")
    confidence: Optional[float] = Field(None, description="Confidence score")
