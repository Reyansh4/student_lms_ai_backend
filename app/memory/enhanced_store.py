"""
Enhanced memory store with Langfuse tracing and hierarchical memory integration
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Literal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.db.session import get_db
from app.db.models import Conversation, Message, ChatMessage
from app.memory.hierarchical_memory import HierarchicalMemory
from app.memory.store import Session as MemorySession, Message as MemoryMessage
from app.config.langfuse_config import (
    MemoryTracker, track_memory_operation, traced_operation, 
    track_function_call, langfuse_manager
)

logger = logging.getLogger(__name__)

class EnhancedMemoryStore:
    """
    Enhanced memory store that integrates hierarchical memory with session management
    and comprehensive Langfuse tracing
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnhancedMemoryStore, cls).__new__(cls)
            cls._instance._sessions: Dict[str, MemorySession] = {}
            cls._instance._messages: Dict[str, List[MemoryMessage]] = {}
            cls._instance._conversations: Dict[str, Conversation] = {}  # session_id -> conversation
            cls._instance._hierarchical_memory = HierarchicalMemory()
            cls._instance.db = None
            cls._instance.langfuse_enabled = langfuse_manager.is_enabled()
            logger.info(f"EnhancedMemoryStore initialized with Langfuse: {cls._instance.langfuse_enabled}")
        return cls._instance

    def set_db_session(self, db_session):
        """Set database session for persistent storage"""
        self.db = db_session

    def create_session(self, name: str, user_id: Optional[str] = None, 
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new memory session with tracing"""
        with traced_operation("Memory Session Creation", user_id=user_id) as trace:
            try:
                session_id = str(uuid.uuid4())
                
                trace.add_span("Session Creation", 
                             {"name": name, "user_id": user_id, "metadata": metadata}, 
                             {"session_id": session_id})
                
                # Create session in database
                db = next(get_db())
                conversation = Conversation(
                    id=session_id,
                    name=name,
                    user_id=user_id,
                    metadata=metadata or {},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                # Track memory operation
                if self.langfuse_enabled:
                    track_memory_operation(
                        "create_session",
                        session_id,
                        {"name": name, "user_id": user_id, "metadata": metadata},
                        {"session_id": session_id, "status": "created"},
                        user_id
                    )
                
                trace.add_span("Database Operation", 
                             {"operation": "insert"}, 
                             {"status": "success"})
                
                logger.info(f"Created memory session: {session_id}")
                
                return {
                    "session_id": session_id,
                    "name": name,
                    "user_id": user_id,
                    "metadata": metadata,
                    "created_at": conversation.created_at.isoformat(),
                    "status": "created"
                }
                
            except Exception as e:
                error_msg = f"Failed to create memory session: {str(e)}"
                logger.error(error_msg)
                trace.finish("error", error_msg)
                raise

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
    ) -> MemorySession:
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
        session = MemorySession(
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

    def get_session(self, session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a memory session with tracing"""
        with traced_operation("Memory Session Retrieval", user_id=user_id) as trace:
            try:
                trace.add_span("Session Lookup", 
                             {"session_id": session_id}, 
                             {"status": "searching"})
                
                db = next(get_db())
                conversation = db.query(Conversation).filter(
                    Conversation.id == session_id
                ).first()
                
                if not conversation:
                    trace.add_span("Session Not Found", 
                                 {"session_id": session_id}, 
                                 {"status": "not_found"})
                    return None
                
                # Track memory operation
                if self.langfuse_enabled:
                    track_memory_operation(
                        "get_session",
                        session_id,
                        {"session_id": session_id},
                        {"session": conversation.__dict__, "status": "found"},
                        user_id
                    )
                
                trace.add_span("Session Found", 
                             {"session_id": session_id}, 
                             {"status": "success"})
                
                return {
                    "session_id": conversation.id,
                    "name": conversation.name,
                    "user_id": conversation.user_id,
                    "metadata": conversation.metadata,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "status": "active"
                }
                
            except Exception as e:
                error_msg = f"Failed to get memory session: {str(e)}"
                logger.error(error_msg)
                trace.finish("error", error_msg)
                return None

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
    ) -> MemoryMessage:
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
        msg = MemoryMessage(
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

    def store_message(self, session_id: str, role: str, content: str, 
                     user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store a message in memory with tracing"""
        with traced_operation("Message Storage", user_id=user_id) as trace:
            try:
                message_id = str(uuid.uuid4())
                
                trace.add_span("Message Creation", 
                             {"session_id": session_id, "role": role, "content": content[:100]}, 
                             {"message_id": message_id})
                
                # Store message in database
                db = next(get_db())
                message = Message(
                    id=message_id,
                    session_id=session_id,
                    role=role,
                    content=content,
                    metadata=metadata or {},
                    created_at=datetime.utcnow()
                )
                
                db.add(message)
                
                # Update conversation timestamp
                conversation = db.query(Conversation).filter(
                    Conversation.id == session_id
                ).first()
                
                if conversation:
                    conversation.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(message)
                
                # Track memory operation
                if self.langfuse_enabled:
                    track_memory_operation(
                        "store_message",
                        session_id,
                        {"role": role, "content": content[:100], "metadata": metadata},
                        {"message_id": message_id, "status": "stored"},
                        user_id
                    )
                
                trace.add_span("Database Operation", 
                             {"operation": "insert_message"}, 
                             {"status": "success"})
                
                logger.info(f"Stored message in session {session_id}: {message_id}")
                
                return {
                    "message_id": message_id,
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata,
                    "created_at": message.created_at.isoformat(),
                    "status": "stored"
                }
                
            except Exception as e:
                error_msg = f"Failed to store message: {str(e)}"
                logger.error(error_msg)
                trace.finish("error", error_msg)
                raise

    def get_history(self, session_id: str) -> List[MemoryMessage]:
        """Get message history for a session (last 10 from memory)"""
        return list(self._messages.get(session_id, []))

    def get_full_conversation_history(self, session_id: str) -> List[ChatMessage]:
        """Get full conversation history from database"""
        if not self.db:
            return []
        
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

    def get_conversation_memory(self, session_id: str, limit: int = 50, 
                               user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversation memory with tracing"""
        with traced_operation("Conversation Memory Retrieval", user_id=user_id) as trace:
            try:
                trace.add_span("Memory Lookup", 
                             {"session_id": session_id, "limit": limit}, 
                             {"status": "searching"})
                
                db = next(get_db())
                messages = db.query(Message).filter(
                    Message.session_id == session_id
                ).order_by(Message.created_at.asc()).limit(limit).all()
                
                # Convert to list of dictionaries
                memory_data = []
                for msg in messages:
                    memory_data.append({
                        "message_id": msg.id,
                        "session_id": msg.session_id,
                        "role": msg.role,
                        "content": msg.content,
                        "metadata": msg.metadata,
                        "created_at": msg.created_at.isoformat()
                    })
                
                # Track memory operation
                if self.langfuse_enabled:
                    track_memory_operation(
                        "get_conversation_memory",
                        session_id,
                        {"session_id": session_id, "limit": limit},
                        {"message_count": len(memory_data), "status": "retrieved"},
                        user_id
                    )
                
                trace.add_span("Memory Retrieved", 
                             {"session_id": session_id}, 
                             {"message_count": len(memory_data)})
                
                logger.info(f"Retrieved {len(memory_data)} messages from session {session_id}")
                
                return memory_data
                
            except Exception as e:
                error_msg = f"Failed to get conversation memory: {str(e)}"
                logger.error(error_msg)
                trace.finish("error", error_msg)
                return []

    def get_hierarchical_context(self, query: str, session_id: str) -> str:
        """Get context from hierarchical memory"""
        return self._hierarchical_memory.get_context(query, session_id)

    def get_session_history(self, session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get session history with tracing"""
        with traced_operation("Session History Retrieval", user_id=user_id) as trace:
            try:
                trace.add_span("History Lookup", 
                             {"session_id": session_id}, 
                             {"status": "searching"})
                
                # Get session info
                session_info = self.get_session(session_id, user_id)
                if not session_info:
                    trace.add_span("Session Not Found", 
                                 {"session_id": session_id}, 
                                 {"status": "not_found"})
                    return {"error": "Session not found"}
                
                # Get messages
                messages = self.get_conversation_memory(session_id, user_id=user_id)
                
                # Track memory operation
                if self.langfuse_enabled:
                    track_memory_operation(
                        "get_session_history",
                        session_id,
                        {"session_id": session_id},
                        {"session_info": session_info, "message_count": len(messages), "status": "retrieved"},
                        user_id
                    )
                
                trace.add_span("History Retrieved", 
                             {"session_id": session_id}, 
                             {"message_count": len(messages)})
                
                return {
                    "session": session_info,
                    "messages": messages,
                    "message_count": len(messages),
                    "status": "retrieved"
                }
                
            except Exception as e:
                error_msg = f"Failed to get session history: {str(e)}"
                logger.error(error_msg)
                trace.finish("error", error_msg)
                return {"error": error_msg}

    def list_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """List user sessions with tracing"""
        with traced_operation("User Sessions List", user_id=user_id) as trace:
            try:
                trace.add_span("Sessions Lookup", 
                             {"user_id": user_id, "limit": limit}, 
                             {"status": "searching"})
                
                db = next(get_db())
                conversations = db.query(Conversation).filter(
                    Conversation.user_id == user_id
                ).order_by(desc(Conversation.updated_at)).limit(limit).all()
                
                # Convert to list of dictionaries
                sessions_data = []
                for conv in conversations:
                    sessions_data.append({
                        "session_id": conv.id,
                        "name": conv.name,
                        "user_id": conv.user_id,
                        "metadata": conv.metadata,
                        "created_at": conv.created_at.isoformat(),
                        "updated_at": conv.updated_at.isoformat()
                    })
                
                # Track memory operation
                if self.langfuse_enabled:
                    track_memory_operation(
                        "list_user_sessions",
                        "user_sessions",
                        {"user_id": user_id, "limit": limit},
                        {"session_count": len(sessions_data), "status": "retrieved"},
                        user_id
                    )
                
                trace.add_span("Sessions Retrieved", 
                             {"user_id": user_id}, 
                             {"session_count": len(sessions_data)})
                
                logger.info(f"Retrieved {len(sessions_data)} sessions for user {user_id}")
                
                return sessions_data
                
            except Exception as e:
                error_msg = f"Failed to list user sessions: {str(e)}"
                logger.error(error_msg)
                trace.finish("error", error_msg)
                return []

    def delete_session(self, session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete a memory session with tracing"""
        with traced_operation("Memory Session Deletion", user_id=user_id) as trace:
            try:
                trace.add_span("Session Deletion", 
                             {"session_id": session_id}, 
                             {"status": "deleting"})
                
                db = next(get_db())
                
                # Delete messages first
                message_count = db.query(Message).filter(
                    Message.session_id == session_id
                ).delete()
                
                # Delete conversation
                conversation = db.query(Conversation).filter(
                    Conversation.id == session_id
                ).first()
                
                if conversation:
                    db.delete(conversation)
                    db.commit()
                    
                    # Track memory operation
                    if self.langfuse_enabled:
                        track_memory_operation(
                            "delete_session",
                            session_id,
                            {"session_id": session_id},
                            {"message_count": message_count, "status": "deleted"},
                            user_id
                        )
                    
                    trace.add_span("Session Deleted", 
                                 {"session_id": session_id}, 
                                 {"message_count": message_count})
                    
                    logger.info(f"Deleted session {session_id} with {message_count} messages")
                    
                    return {
                        "session_id": session_id,
                        "message_count": message_count,
                        "status": "deleted"
                    }
                else:
                    trace.add_span("Session Not Found", 
                                 {"session_id": session_id}, 
                                 {"status": "not_found"})
                    return {"error": "Session not found"}
                
            except Exception as e:
                error_msg = f"Failed to delete session: {str(e)}"
                logger.error(error_msg)
                trace.finish("error", error_msg)
                raise

    def cleanup_old_sessions(self, days_old: int = 30, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Clean up old sessions with tracing"""
        with traced_operation("Session Cleanup", user_id=user_id) as trace:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_old)
                
                trace.add_span("Cleanup Initiated", 
                             {"days_old": days_old, "cutoff_date": cutoff_date.isoformat()}, 
                             {"status": "processing"})
                
                db = next(get_db())
                
                # Find old sessions
                old_conversations = db.query(Conversation).filter(
                    Conversation.updated_at < cutoff_date
                ).all()
                
                deleted_sessions = 0
                deleted_messages = 0
                
                for conv in old_conversations:
                    # Delete messages
                    message_count = db.query(Message).filter(
                        Message.session_id == conv.id
                    ).delete()
                    
                    # Delete conversation
                    db.delete(conv)
                    deleted_sessions += 1
                    deleted_messages += message_count
                
                db.commit()
                
                # Track memory operation
                if self.langfuse_enabled:
                    track_memory_operation(
                        "cleanup_old_sessions",
                        "cleanup",
                        {"days_old": days_old, "cutoff_date": cutoff_date.isoformat()},
                        {"deleted_sessions": deleted_sessions, "deleted_messages": deleted_messages, "status": "completed"},
                        user_id
                    )
                
                trace.add_span("Cleanup Completed", 
                             {"days_old": days_old}, 
                             {"deleted_sessions": deleted_sessions, "deleted_messages": deleted_messages})
                
                logger.info(f"Cleanup completed: {deleted_sessions} sessions, {deleted_messages} messages")
                
                return {
                    "deleted_sessions": deleted_sessions,
                    "deleted_messages": deleted_messages,
                    "cutoff_date": cutoff_date.isoformat(),
                    "status": "completed"
                }
                
            except Exception as e:
                error_msg = f"Failed to cleanup old sessions: {str(e)}"
                logger.error(error_msg)
                trace.finish("error", error_msg)
                raise

    def get_memory_stats(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        if session_id:
            # Get session-specific stats
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
        else:
            # Get global stats with tracing
            with traced_operation("Memory Statistics", user_id=user_id) as trace:
                try:
                    trace.add_span("Stats Collection", 
                                 {"user_id": user_id}, 
                                 {"status": "collecting"})
                    
                    db = next(get_db())
                    
                    # Get total sessions
                    total_sessions = db.query(Conversation).count()
                    
                    # Get total messages
                    total_messages = db.query(Message).count()
                    
                    # Get user-specific stats if user_id provided
                    user_stats = {}
                    if user_id:
                        user_sessions = db.query(Conversation).filter(
                            Conversation.user_id == user_id
                        ).count()
                        user_messages = db.query(Message).join(Conversation).filter(
                            Conversation.user_id == user_id
                        ).count()
                        user_stats = {
                            "user_sessions": user_sessions,
                            "user_messages": user_messages
                        }
                    
                    stats = {
                        "total_sessions": total_sessions,
                        "total_messages": total_messages,
                        "user_stats": user_stats,
                        "langfuse_enabled": self.langfuse_enabled,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Track memory operation
                    if self.langfuse_enabled:
                        track_memory_operation(
                            "get_memory_stats",
                            "stats",
                            {"user_id": user_id},
                            {"stats": stats, "status": "retrieved"},
                            user_id
                        )
                    
                    trace.add_span("Stats Retrieved", 
                                 {"user_id": user_id}, 
                                 {"total_sessions": total_sessions, "total_messages": total_messages})
                    
                    return stats
                    
                except Exception as e:
                    error_msg = f"Failed to get memory stats: {str(e)}"
                    logger.error(error_msg)
                    trace.finish("error", error_msg)
                    return {"error": error_msg}

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

    def fuzzy_search(self, session_id: str, term: str) -> List[MemoryMessage]:
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