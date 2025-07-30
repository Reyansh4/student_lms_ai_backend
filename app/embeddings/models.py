"""
Unified embedding storage model for all entities
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UUID, JSON, Float, func, Index, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

class EmbeddingStore(Base):
    """
    Unified embedding storage for all models in the system.
    Stores embeddings with rich metadata for effective semantic retrieval.
    """
    __tablename__ = "embedding_store"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)  # 'activity', 'question', 'ai_response', etc.
    entity_id = Column(UUID, nullable=False)  # Foreign key to original entity
    content_text = Column(Text, nullable=False)  # Text to be embedded
    embedding_vector = Column(JSON, nullable=False)  # Stored as JSON array
    metadata = Column(JSON, nullable=False)  # Rich metadata for filtering
    embedding_model = Column(String(100), nullable=False)  # Model used for embedding
    embedding_dimension = Column(Integer, nullable=False)  # Dimension of embedding
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_entity_type_id', 'entity_type', 'entity_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_embedding_model', 'embedding_model'),
    )
    
    def __repr__(self):
        return f"<EmbeddingStore(entity_type='{self.entity_type}', entity_id='{self.entity_id}')>"
    
    @property
    def embedding_list(self) -> List[float]:
        """Convert JSON embedding to list"""
        return self.embedding_vector if isinstance(self.embedding_vector, list) else []
    
    @embedding_list.setter
    def embedding_list(self, value: List[float]):
        """Set embedding as JSON"""
        self.embedding_vector = value
    
    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """Get metadata value safely"""
        return self.metadata.get(key, default) if self.metadata else default
    
    def set_metadata_value(self, key: str, value: Any) -> None:
        """Set metadata value safely"""
        if not self.metadata:
            self.metadata = {}
        self.metadata[key] = value 