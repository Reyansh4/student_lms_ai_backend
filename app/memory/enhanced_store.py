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
from app.models.conversation import Conversation
from app.models.chat_message import ChatMessage
from app.models.activity_chat import ActivityChat

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
            cls._instance._conversations: Dict[str, Conversation] = {}  # session_id -> conversation
            cls._instance._hierarchical_memory = HierarchicalMemory()
            cls._instance.db = None
        return cls._instance

    def set_db_session(self, db_session):
        """Set database session for persistent storage"""
        self.db = db_session

    def get_or_create_conversation(
        self,
        session_id: str,
        user_id: str,
        title: Optional[str] = None,
        conversation_type: str = "general",
        activity_id: Optional[str] = None
    ) -> Conversation:
        """Get or create a conversation for a session"""
        if session_id in self._conversations:
            return self._conversations[session_id]
        
        if self.db:
            # Try to find existing conversation in database
            existing_conv = self.db.query(Conversation).filter(
                Conversation.session_id == session_id
            ).first()
            
            if existing_conv:
                self._conversations[session_id] = existing_conv
                return existing_conv
        
        # Create new conversation
        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
            title=title or f"Conversation {session_id[:8]}",
            conversation_type=conversation_type,
            activity_id=activity_id
        )
        
        if self.db:
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            logger.info(f"Created new conversation in DB: {conversation.id}")
        
        self._conversations[session_id] = conversation
        return conversation

    def get_or_create_session(
        self,
        user_id: str,
        name: Optional[str] = None,
    ) -> Session:
        """
        Get or create a session for a user, maintaining continuity
        """
        # Check if user already has an active session
        for session_id, session in self._sessions.items():
            if session.user_id == user_id:
                # Update session timestamp and return existing
                session.updated_at = datetime.now()
                logger.info(f"Reusing existing session {session_id} for user {user_id}")
                return session
        
        # Create new session only if none exists
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
        activity_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Message:
        """Add message to both session store and hierarchical memory"""
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")
        
        # Get or create conversation
        if user_id:
            conversation = self.get_or_create_conversation(
                session_id=session_id,
                user_id=user_id,
                activity_id=activity_id,
                conversation_type="activity" if activity_id else "general"
            )
        
        # Create message for session store (in-memory)
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
        
        # Add to in-memory storage (last 10 messages only)
        if session_id not in self._messages:
            self._messages[session_id] = []
        
        self._messages[session_id].append(msg)
        
        # Keep only last 10 messages in memory for fast access
        if len(self._messages[session_id]) > 10:
            self._messages[session_id] = self._messages[session_id][-10:]
        
        # Store in database if available (persistent storage)
        if self.db and user_id and 'conversation' in locals():
            db_message = ChatMessage(
                conversation_id=conversation.id,
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                intent=intent,
                topic=topic,
                message_metadata=metadata or {},
                activity_id=activity_id
            )
            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)
            logger.debug(f"Stored message in database: {db_message.id}")
        
        # Update session timestamp
        self._sessions[session_id].updated_at = timestamp
        
        # Add to hierarchical memory if it's a user message
        if role == "user":
            self._temp_user_message = content
            self._temp_user_metadata = metadata or {}
        elif role == "assistant" and hasattr(self, '_temp_user_message'):
            self._hierarchical_memory.add_message(
                user_input=self._temp_user_message,
                ai_response=content,
                session_id=session_id,
                metadata=self._temp_user_metadata
            )
            delattr(self, '_temp_user_message')
            delattr(self, '_temp_user_metadata')
        
        logger.debug(f"Added {role} message to session {session_id}")
        return msg

    def get_history(self, session_id: str) -> List[Message]:
        """Get message history for a session (last 10 from memory)"""
        return list(self._messages.get(session_id, []))

    def get_full_conversation_history(self, session_id: str) -> List[ChatMessage]:
        """Get full conversation history from database"""
        if not self.db:
            return []
        
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

    def get_conversation_memory(self, session_id: str) -> List[Message]:
        """Get last 10 messages for memory context"""
        return self.get_history(session_id)

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
        
        conversation_stats = {
            "conversation_id": self._conversations.get(session_id, {}).id if session_id in self._conversations else None,
            "conversation_type": self._conversations.get(session_id, {}).conversation_type if session_id in self._conversations else None,
        }
        
        hierarchical_stats = self._hierarchical_memory.get_memory_stats(session_id)
        
        return {
            "session": session_stats,
            "conversation": conversation_stats,
            "hierarchical": hierarchical_stats
        }

    def clear_session_memory(self, session_id: str) -> None:
        """Clear both session and hierarchical memory for a session"""
        if session_id in self._messages:
            del self._messages[session_id]
        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._conversations:
            del self._conversations[session_id]
        
        self._hierarchical_memory.clear_memory(session_id)
        logger.info(f"Cleared all memory for session {session_id}")

    def fuzzy_search(self, session_id: str, term: str) -> List[Message]:
        """Search messages in session store (last 10 messages)"""
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