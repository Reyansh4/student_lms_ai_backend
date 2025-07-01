# app/api/memory.py

from typing import List, Optional, Literal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.memory.store import InMemoryStore, Session, Message
from app.api.deps import get_current_user
from app.models.user import User
from functools import lru_cache

# import for embeddings
from app.core.azure_config import load_azure_config
from openai import AsyncAzureOpenAI

router = APIRouter(prefix="/memory", tags=["memory"])


# Load Azure config & create a dedicated embeddings client once
azure_config = load_azure_config()
emb_client = AsyncAzureOpenAI(
    api_key=azure_config.api_key,
    azure_endpoint=azure_config.endpoint,
    api_version=azure_config.api_version
)

# —— Pydantic schemas —— 

class SessionSchema(BaseModel):
    session_id: str
    user_id: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class MessageSchema(BaseModel):
    message_id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    embedding: Optional[List[float]]
    intent: Optional[str]
    topic: Optional[str]

    class Config:
        orm_mode = True

class CreateMessageRequest(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    intent: Optional[str] = None
    topic: Optional[str] = None

# —— Endpoints —— 

@lru_cache(maxsize=None)
def get_store() -> InMemoryStore:
    return InMemoryStore()

@router.post(
    "/sessions",
    response_model=SessionSchema,
    summary="Create a new session for the current user",
)
def create_session(
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    store: InMemoryStore = Depends(get_store),    # now cached
):
    session = store.get_or_create_session(str(current_user.id), name=name)
    return session

@router.post(
    "/sessions/{session_id}/messages",
    response_model=MessageSchema,
    summary="Add a message (user or assistant) to a session",
)
def add_message(
    session_id: str,
    req: CreateMessageRequest,
    current_user: User = Depends(get_current_user),
    store: InMemoryStore = Depends(get_store),
):
    session = store._sessions.get(session_id)
    if not session or session.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
    msg = store.add_message(
        session_id,
        role=req.role,
        content=req.content,
        intent=req.intent,
        topic=req.topic,
    )
    return msg

@router.get(
    "/sessions/{session_id}/history",
    response_model=List[MessageSchema],
    summary="Fetch full message history for a session",
)
def get_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    store: InMemoryStore = Depends(get_store),
):
    session = store._sessions.get(session_id)
    if not session or session.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
    return store.get_history(session_id)

@router.get(
    "/sessions/{session_id}/search",
    response_model=List[MessageSchema],
    summary="Search messages in a session (fuzzy or semantic)",
)
async def search_messages(
    session_id: str,
    q: str = Query(..., description="Search term or query text"),
    type: Literal["fuzzy", "semantic"] = Query("fuzzy"),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    store: InMemoryStore = Depends(get_store),
):
    session = store._sessions.get(session_id)
    if not session or session.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")

    if type == "fuzzy":
        return store.fuzzy_search(session_id, q)

    # ── Semantic search ──────────────────────────────────────────────────────────
    # 1) Embed the query text
    embed_resp = await emb_client.embeddings.create(
        model=azure_config.embedding_deployment or azure_config.deployment,
        input=[q]
    )
    query_embedding = embed_resp.data[0].embedding

    # 2) Fetch top_k messages by cosine similarity
    sem_results = store.semantic_search(session_id, query_embedding, top_k)

    # 3) Return only the Message objects (dropping scores)
    return [msg for msg, score in sem_results]
