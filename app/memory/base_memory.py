"""
Base memory strategy for hierarchical memory system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MemoryMessage:
    """Represents a message in memory"""
    user_input: str
    ai_response: str
    timestamp: datetime
    session_id: str
    metadata: Dict[str, Any]

class BaseMemoryStrategy(ABC):
    """Abstract base class for memory strategies"""
    
    @abstractmethod
    def add_message(self, user_input: str, ai_response: str, session_id: str = "default", metadata: Dict[str, Any] = None) -> None:
        """Add a message to memory"""
        pass
    
    @abstractmethod
    def get_context(self, query: str, session_id: str = "default") -> str:
        """Get context from memory based on query"""
        pass
    
    @abstractmethod
    def clear_memory(self, session_id: str = "default") -> None:
        """Clear memory for a session"""
        pass
    
    @abstractmethod
    def get_memory_stats(self, session_id: str = "default") -> Dict[str, Any]:
        """Get memory statistics"""
        pass 