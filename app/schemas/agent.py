from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

class AgentInput(BaseModel):
    prompt: str = Field(..., description="User input prompt")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentOutput(BaseModel):
    intent: str = Field(..., description="Detected user intent")
    result: Dict[str, Any] = Field(..., description="Agent response")