"""
Sliding window memory for working memory (short-term)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from app.memory.base_memory import BaseMemoryStrategy, MemoryMessage
from app.core.logger import get_logger

logger = get_logger(__name__)

class SlidingWindowMemory(BaseMemoryStrategy):
    """Sliding window memory for fast, short-term working memory"""
    
    def __init__(self, window_size: int = 5):
        """
        Initialize sliding window memory
        
        Args:
            window_size: Number of recent messages to keep in working memory
        """
        self.window_size = window_size
        self.memories: Dict[str, List[MemoryMessage]] = {}
        logger.info(f"Initialized SlidingWindowMemory with window_size={window_size}")
    
    def add_message(self, user_input: str, ai_response: str, session_id: str = "default", metadata: Dict[str, Any] = None) -> None:
        """Add message to working memory with sliding window"""
        if session_id not in self.memories:
            self.memories[session_id] = []
        
        message = MemoryMessage(
            user_input=user_input,
            ai_response=ai_response,
            timestamp=datetime.now(),
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # Add to the beginning (most recent first)
        self.memories[session_id].insert(0, message)
        
        # Keep only the most recent messages within window size
        if len(self.memories[session_id]) > self.window_size:
            self.memories[session_id] = self.memories[session_id][:self.window_size]
        
        logger.debug(f"Added message to working memory for session {session_id}. Total messages: {len(self.memories[session_id])}")
    
    def get_context(self, query: str, session_id: str = "default") -> str:
        """Get recent conversation context from working memory"""
        if session_id not in self.memories or not self.memories[session_id]:
            return "### Recent Conversation (Working Memory):\nNo recent conversation history."
        
        # Get recent messages (most recent first, then reverse for chronological order)
        recent_messages = self.memories[session_id][:self.window_size]
        recent_messages.reverse()  # Show in chronological order
        
        context_lines = ["### Recent Conversation (Working Memory):"]
        
        for i, message in enumerate(recent_messages, 1):
            context_lines.append(f"Turn {i}:")
            context_lines.append(f"User: {message.user_input}")
            context_lines.append(f"Assistant: {message.ai_response}")
            context_lines.append("")
        
        return "\n".join(context_lines)
    
    def clear_memory(self, session_id: str = "default") -> None:
        """Clear working memory for a session"""
        if session_id in self.memories:
            del self.memories[session_id]
            logger.info(f"Cleared working memory for session {session_id}")
    
    def get_memory_stats(self, session_id: str = "default") -> Dict[str, Any]:
        """Get working memory statistics"""
        messages = self.memories.get(session_id, [])
        return {
            "type": "sliding_window",
            "session_id": session_id,
            "message_count": len(messages),
            "window_size": self.window_size,
            "oldest_message": messages[-1].timestamp if messages else None,
            "newest_message": messages[0].timestamp if messages else None
        } 