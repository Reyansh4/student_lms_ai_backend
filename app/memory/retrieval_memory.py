"""
Retrieval memory for long-term memory using embeddings
"""

import json
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.memory.base_memory import BaseMemoryStrategy, MemoryMessage
from app.core.logger import get_logger
from app.config import load_azure_config
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings

logger = get_logger(__name__)

class RetrievalMemory(BaseMemoryStrategy):
    """Retrieval-based memory for long-term storage using embeddings"""
    
    def __init__(self, k: int = 5, embedding_dim: int = 1536):
        """
        Initialize retrieval memory
        
        Args:
            k: Number of most relevant memories to retrieve
            embedding_dim: Dimension of embedding vectors
        """
        self.k = k
        self.embedding_dim = embedding_dim
        self.memories: Dict[str, List[MemoryMessage]] = {}
        self.embeddings: Dict[str, List[np.ndarray]] = {}
        
        # Initialize Azure OpenAI for embeddings
        try:
            azure_config = load_azure_config()
            self.embedding_model = AzureOpenAIEmbeddings(
                openai_api_version=azure_config.api_version,
                azure_deployment=azure_config.embedding_deployment or "text-embedding-ada-002",
                azure_endpoint=azure_config.endpoint,
                api_key=azure_config.api_key,
                chunk_size=1000  # Add the missing chunk_size parameter
            )
            logger.info(f"Initialized RetrievalMemory with k={k}, embedding_dim={embedding_dim}")
        except Exception as e:
            logger.warning(f"Failed to initialize embedding model: {e}")
            self.embedding_model = None
    
    def add_message(self, user_input: str, ai_response: str, session_id: str = "default", metadata: Dict[str, Any] = None) -> None:
        """Add message to long-term memory with embedding"""
        if session_id not in self.memories:
            self.memories[session_id] = []
            self.embeddings[session_id] = []
        
        message = MemoryMessage(
            user_input=user_input,
            ai_response=ai_response,
            timestamp=datetime.now(),
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # Add to memory
        self.memories[session_id].append(message)
        
        # Create embedding for retrieval
        if self.embedding_model:
            try:
                # Combine user input and AI response for embedding
                combined_text = f"User: {user_input}\nAssistant: {ai_response}"
                embedding = self.embedding_model.embed_query(combined_text)
                self.embeddings[session_id].append(np.array(embedding))
                logger.debug(f"Added message to long-term memory for session {session_id}. Total messages: {len(self.memories[session_id])}")
            except Exception as e:
                logger.error(f"Failed to create embedding: {e}")
                # Add zero vector as fallback
                self.embeddings[session_id].append(np.zeros(self.embedding_dim))
        else:
            # Add zero vector if no embedding model
            self.embeddings[session_id].append(np.zeros(self.embedding_dim))
    
    def get_context(self, query: str, session_id: str = "default") -> str:
        """Get relevant context from long-term memory using semantic search"""
        if session_id not in self.memories or not self.memories[session_id]:
            return "### Retrieved Long-Term Memories:\nNo long-term memories available."
        
        if not self.embedding_model:
            # Fallback: return recent messages
            recent_messages = self.memories[session_id][-self.k:]
            context_lines = ["### Retrieved Long-Term Memories (Recent):"]
            for i, message in enumerate(recent_messages, 1):
                context_lines.append(f"Memory {i}:")
                context_lines.append(f"User: {message.user_input}")
                context_lines.append(f"Assistant: {message.ai_response}")
                context_lines.append("")
            return "\n".join(context_lines)
        
        try:
            # Create query embedding
            query_embedding = np.array(self.embedding_model.embed_query(query))
            
            # Calculate similarities
            similarities = []
            for i, memory_embedding in enumerate(self.embeddings[session_id]):
                similarity = np.dot(query_embedding, memory_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(memory_embedding)
                )
                similarities.append((i, similarity))
            
            # Sort by similarity and get top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = [idx for idx, _ in similarities[:self.k]]
            
            # Build context from most relevant memories
            context_lines = ["### Retrieved Long-Term Memories:"]
            for i, idx in enumerate(top_indices, 1):
                message = self.memories[session_id][idx]
                similarity = similarities[i-1][1]
                context_lines.append(f"Relevant Memory {i} (similarity: {similarity:.3f}):")
                context_lines.append(f"User: {message.user_input}")
                context_lines.append(f"Assistant: {message.ai_response}")
                context_lines.append("")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"Failed to retrieve from long-term memory: {e}")
            return "### Retrieved Long-Term Memories:\nError retrieving long-term memories."
    
    def clear_memory(self, session_id: str = "default") -> None:
        """Clear long-term memory for a session"""
        if session_id in self.memories:
            del self.memories[session_id]
        if session_id in self.embeddings:
            del self.embeddings[session_id]
        logger.info(f"Cleared long-term memory for session {session_id}")
    
    def get_memory_stats(self, session_id: str = "default") -> Dict[str, Any]:
        """Get long-term memory statistics"""
        messages = self.memories.get(session_id, [])
        embeddings_count = len(self.embeddings.get(session_id, []))
        return {
            "type": "retrieval",
            "session_id": session_id,
            "message_count": len(messages),
            "embedding_count": embeddings_count,
            "k": self.k,
            "embedding_dim": self.embedding_dim,
            "oldest_message": messages[0].timestamp if messages else None,
            "newest_message": messages[-1].timestamp if messages else None
        } 