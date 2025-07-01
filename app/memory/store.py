from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Tuple, Literal
import uuid
import numpy as np

@dataclass
class Session:
    session_id: str
    user_id: str
    name: str
    created_at: datetime
    updated_at: datetime

@dataclass
class Message:
    message_id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    embedding: Optional[List[float]] = None
    intent: Optional[str] = None
    topic: Optional[str] = None

class InMemoryStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InMemoryStore, cls).__new__(cls)
            cls._instance._sessions: Dict[str, Session] = {}
            cls._instance._messages: Dict[str, List[Message]] = {}
        return cls._instance

    def get_or_create_session(
        self,
        user_id: str,
        name: Optional[str] = None,
    ) -> Session:
        """
        Always creates a new session for simplicity.
        Accepts an optional `name` to label the session.
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()
        session = Session(
            session_id=session_id,
            user_id=user_id,
            name=name or session_id,
            created_at=now,
            updated_at=now,
        )
        self._sessions[session_id] = session
        self._messages[session_id] = []
        return session

    def add_message(
        self,
        session_id: str,
        role: Literal["user", "assistant"],
        content: str,
        intent: Optional[str] = None,
        topic: Optional[str] = None,
        embedding: Optional[List[float]] = None,
    ) -> Message:
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")
        mid = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        msg = Message(
            message_id=mid,
            session_id=session_id,
            role=role,
            content=content,
            timestamp=timestamp,
            embedding=embedding,
            intent=intent,
            topic=topic,
        )
        self._messages[session_id].append(msg)
        # Update session timestamp
        self._sessions[session_id].updated_at = timestamp
        return msg

    def get_history(self, session_id: str) -> List[Message]:
        return list(self._messages.get(session_id, []))

    def fuzzy_search(self, session_id: str, term: str) -> List[Message]:
        term_lower = term.lower()
        return [m for m in self._messages.get(session_id, []) if term_lower in m.content.lower()]

    def semantic_search(
        self,
        session_id: str,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Tuple[Message, float]]:
        messages = self._messages.get(session_id, [])
        results: List[Tuple[Message, float]] = []
        q_emb = np.array(query_embedding)
        for m in messages:
            if m.embedding is not None:
                m_emb = np.array(m.embedding)
                # cosine similarity
                sim = float(
                    np.dot(q_emb, m_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(m_emb) + 1e-8)
                )
                results.append((m, sim))
        # sort descending by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
