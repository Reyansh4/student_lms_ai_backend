"""
Enhanced store that integrates with hierarchical memory system
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Tuple, Literal, Any
import uuid
import numpy as np
from app.memory.hierarchical_memory import HierarchicalMemory
from app.core.logger import get_logger

logger = get_logger(__name__)

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
    metadata: Dict[str, Any] = field(default_factory=dict)

class EnhancedMemoryStore:
    """
    Enhanced memory store that integrates hierarchical memory with session management
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnhancedMemoryStore, cls).__new__(cls)
            cls._instance._sessions: Dict[str, Session] = {}
            cls._instance._messages: Dict[str, List[Message]] = {}
            cls._instance._hierarchical_memory = HierarchicalMemory()
        return cls._instance

    def get_or_create_session(
        self,
        user_id: str,
        name: Optional[str] = None,
    ) -> Session:
        """
        Get or create a session for a user
        """
        # For simplicity, always create a new session
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
        logger.info(f"Created new session {session_id} for user {user_id}")
        return session

    def add_message(
        self,
        session_id: str,
        role: Literal["user", "assistant"],
        content: str,
        intent: Optional[str] = None,
        topic: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Add message to both session store and hierarchical memory"""
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")
        
        # Create message for session store
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
            metadata=metadata or {}
        )
        self._messages[session_id].append(msg)
        
        # Update session timestamp
        self._sessions[session_id].updated_at = timestamp
        
        # Add to hierarchical memory if it's a user message
        # (We'll add the assistant response when it comes)
        if role == "user":
            # Store user message temporarily
            self._temp_user_message = content
            self._temp_user_metadata = metadata or {}
        elif role == "assistant" and hasattr(self, '_temp_user_message'):
            # Add the complete interaction to hierarchical memory
            self._hierarchical_memory.add_message(
                user_input=self._temp_user_message,
                ai_response=content,
                session_id=session_id,
                metadata=self._temp_user_metadata
            )
            # Clear temporary storage
            delattr(self, '_temp_user_message')
            delattr(self, '_temp_user_metadata')
        
        logger.debug(f"Added {role} message to session {session_id}")
        return msg

    def get_history(self, session_id: str) -> List[Message]:
        """Get message history for a session"""
        return list(self._messages.get(session_id, []))

    def get_hierarchical_context(self, query: str, session_id: str) -> str:
        """Get context from hierarchical memory"""
        return self._hierarchical_memory.get_context(query, session_id)

    def get_memory_stats(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        session_stats = {
            "session_id": session_id,
            "session_messages": len(self._messages.get(session_id, [])),
            "session_created": self._sessions.get(session_id, {}).created_at if session_id in self._sessions else None,
            "session_updated": self._sessions.get(session_id, {}).updated_at if session_id in self._sessions else None,
        }
        
        hierarchical_stats = self._hierarchical_memory.get_memory_stats(session_id)
        
        return {
            "session": session_stats,
            "hierarchical": hierarchical_stats
        }

    def clear_session_memory(self, session_id: str) -> None:
        """Clear both session and hierarchical memory for a session"""
        if session_id in self._messages:
            del self._messages[session_id]
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        self._hierarchical_memory.clear_memory(session_id)
        logger.info(f"Cleared all memory for session {session_id}")

    def fuzzy_search(self, session_id: str, term: str) -> List[Message]:
        """Search messages in session store"""
        term_lower = term.lower()
        return [m for m in self._messages.get(session_id, []) if term_lower in m.content.lower()]

    def get_promotion_keywords(self) -> List[str]:
        """Get promotion keywords from hierarchical memory"""
        return self._hierarchical_memory.get_promotion_keywords()

    def add_promotion_keyword(self, keyword: str) -> None:
        """Add a promotion keyword to hierarchical memory"""
        self._hierarchical_memory.add_promotion_keyword(keyword)

    def remove_promotion_keyword(self, keyword: str) -> None:
        """Remove a promotion keyword from hierarchical memory"""
        self._hierarchical_memory.remove_promotion_keyword(keyword)

# Global instance for easy access
enhanced_memory_store = EnhancedMemoryStore() 