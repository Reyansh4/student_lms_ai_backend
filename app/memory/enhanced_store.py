"""
Enhanced memory store with Langfuse tracing for comprehensive observability
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.db.session import get_db
from app.db.models import Conversation, Message
from app.config.langfuse_config import (
    MemoryTracker, track_memory_operation, traced_operation, 
    track_function_call, langfuse_manager
)

logger = logging.getLogger(__name__)

class EnhancedMemoryStore:
    """Enhanced memory store with comprehensive Langfuse tracing"""
    
    def __init__(self):
        self.langfuse_enabled = langfuse_manager.is_enabled()
        logger.info(f"EnhancedMemoryStore initialized with Langfuse: {self.langfuse_enabled}")
    
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
    
    def get_memory_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory statistics with tracing"""
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