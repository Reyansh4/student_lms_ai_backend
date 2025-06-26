"""
FastAPI router for the Agent endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from app.agent.chat import run_agent

router = APIRouter()

class AgentInput(BaseModel):
    prompt: str = Field(..., description="User input prompt")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentOutput(BaseModel):
    intent: str = Field(..., description="Detected user intent")
    result: Dict[str, Any] = Field(..., description="Agent response")

@router.post("/agent/chat", response_model=AgentOutput)
async def agent_chat(input: AgentInput):
    try:
        # Use the new run_agent entry point
        response = await run_agent(input.dict())
        return AgentOutput(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))