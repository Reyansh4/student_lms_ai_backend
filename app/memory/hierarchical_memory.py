"""
Hierarchical memory system combining working and long-term memory
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from app.memory.base_memory import BaseMemoryStrategy, MemoryMessage
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.memory.retrieval_memory import RetrievalMemory
from app.core.logger import get_logger

logger = get_logger(__name__)

class HierarchicalMemory(BaseMemoryStrategy):
    """
    Hierarchical memory system that combines multiple memory types:
    - Working Memory (SlidingWindowMemory): Fast, short-term memory
    - Long-Term Memory (RetrievalMemory): Durable, semantic search-based memory
    """
    
    def __init__(self, window_size: int = 5, k: int = 5, embedding_dim: int = 1536):
        """
        Initialize hierarchical memory system
        
        Args:
            window_size: Size of working memory window
            k: Number of relevant memories to retrieve from long-term memory
            embedding_dim: Dimension of embedding vectors
        """
        logger.info("Initializing Hierarchical Memory...")
        
        # Level 1: Fast, short-term working memory using sliding window
        self.working_memory = SlidingWindowMemory(window_size=window_size)
        
        # Level 2: Slower, durable long-term memory using retrieval system
        self.long_term_memory = RetrievalMemory(k=k, embedding_dim=embedding_dim)
        
        # Keywords that trigger promotion from working to long-term memory
        self.promotion_keywords = [
            "remember", "rule", "preference", "always", "never", "allergic",
            "important", "critical", "save", "store", "keep", "note",
            "user id", "password", "username", "email", "phone", "address",
            "preference", "setting", "configuration", "favorite", "like", "dislike"
        ]
        
        # Learning-specific keywords for educational context
        self.learning_keywords = [
            "learn", "study", "practice", "understand", "explain", "teach",
            "concept", "topic", "subject", "lesson", "course", "assignment",
            "quiz", "test", "exam", "homework", "project", "research"
        ]
        
        # Combine all promotion keywords
        self.all_promotion_keywords = self.promotion_keywords + self.learning_keywords
        
        logger.info(f"Hierarchical Memory initialized with {len(self.all_promotion_keywords)} promotion keywords")
    
    def add_message(self, user_input: str, ai_response: str, session_id: str = "default", metadata: Dict[str, Any] = None) -> None:
        """
        Add message to hierarchical memory system
        
        All messages go to working memory, and important ones are promoted to long-term memory
        """
        # All interactions are added to fast, short-term working memory
        self.working_memory.add_message(user_input, ai_response, session_id, metadata)
        
        # Check if message should be promoted to long-term memory
        should_promote = self._should_promote_to_long_term(user_input, ai_response, metadata)
        
        if should_promote:
            logger.info(f"--- [Hierarchical Memory: Promoting message to long-term storage.] ---")
            logger.info(f"User input: {user_input[:100]}...")
            
            # Add to long-term memory with enhanced metadata
            enhanced_metadata = metadata or {}
            enhanced_metadata.update({
                "promoted": True,
                "promotion_reason": should_promote,
                "promotion_timestamp": datetime.now().isoformat()
            })
            
            self.long_term_memory.add_message(user_input, ai_response, session_id, enhanced_metadata)
    
    def _should_promote_to_long_term(self, user_input: str, ai_response: str, metadata: Dict[str, Any] = None) -> str:
        """
        Determine if a message should be promoted to long-term memory
        
        Returns:
            Reason for promotion or empty string if not promoted
        """
        input_lower = user_input.lower()
        
        # Check for promotion keywords
        for keyword in self.all_promotion_keywords:
            if keyword in input_lower:
                return f"Contains promotion keyword: '{keyword}'"
        
        # Check for explicit memory requests
        memory_indicators = [
            "remember this", "save this", "keep this", "store this",
            "don't forget", "make a note", "write this down"
        ]
        
        for indicator in memory_indicators:
            if indicator in input_lower:
                return f"Contains memory indicator: '{indicator}'"
        
        # Check for personal information patterns
        personal_patterns = [
            r"\b[A-Z]{2,3}-\d{4,}\b",  # User IDs like AX-7890
            r"\b\d{3}-\d{3}-\d{4}\b",  # Phone numbers
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email addresses
        ]
        
        import re
        for pattern in personal_patterns:
            if re.search(pattern, user_input):
                return "Contains personal information pattern"
        
        # Check for learning-specific content
        if any(keyword in input_lower for keyword in self.learning_keywords):
            return "Contains learning-related content"
        
        # Check metadata for explicit promotion flags
        if metadata and metadata.get("promote_to_long_term"):
            return "Explicitly flagged for promotion"
        
        return ""  # No promotion
    
    def get_context(self, query: str, session_id: str = "default") -> str:
        """
        Get context from hierarchical memory system
        
        Combines relevant information from both working and long-term memory
        """
        # Get context from both memory systems
        working_context = self.working_memory.get_context(query, session_id)
        long_term_context = self.long_term_memory.get_context(query, session_id)
        
        # Combine contexts with clear labeling
        combined_context = f"{long_term_context}\n\n{working_context}"
        
        logger.debug(f"Retrieved hierarchical context for session {session_id}")
        logger.debug(f"Working memory messages: {self.working_memory.get_memory_stats(session_id)['message_count']}")
        logger.debug(f"Long-term memory messages: {self.long_term_memory.get_memory_stats(session_id)['message_count']}")
        
        return combined_context
    
    def clear_memory(self, session_id: str = "default") -> None:
        """Clear both working and long-term memory for a session"""
        self.working_memory.clear_memory(session_id)
        self.long_term_memory.clear_memory(session_id)
        logger.info(f"Cleared hierarchical memory for session {session_id}")
    
    def get_memory_stats(self, session_id: str = "default") -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        working_stats = self.working_memory.get_memory_stats(session_id)
        long_term_stats = self.long_term_memory.get_memory_stats(session_id)
        
        return {
            "type": "hierarchical",
            "session_id": session_id,
            "working_memory": working_stats,
            "long_term_memory": long_term_stats,
            "total_messages": working_stats["message_count"] + long_term_stats["message_count"],
            "promotion_keywords_count": len(self.all_promotion_keywords)
        }
    
    def get_promotion_keywords(self) -> List[str]:
        """Get list of promotion keywords"""
        return self.all_promotion_keywords.copy()
    
    def add_promotion_keyword(self, keyword: str) -> None:
        """Add a new promotion keyword"""
        if keyword not in self.all_promotion_keywords:
            self.all_promotion_keywords.append(keyword)
            logger.info(f"Added promotion keyword: '{keyword}'")
    
    def remove_promotion_keyword(self, keyword: str) -> None:
        """Remove a promotion keyword"""
        if keyword in self.all_promotion_keywords:
            self.all_promotion_keywords.remove(keyword)
            logger.info(f"Removed promotion keyword: '{keyword}'") 