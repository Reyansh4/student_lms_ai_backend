"""
Main embedding service for unified embedding management
"""

from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import numpy as np
from datetime import datetime

from app.config import load_azure_config
from app.core.logger import get_logger
from app.embeddings.models import EmbeddingStore
from app.embeddings.extractors import extract_content_from_entity
from langchain_openai import AzureOpenAIEmbeddings

logger = get_logger(__name__)

class EmbeddingService:
    """
    Unified embedding service for all models in the system.
    Handles embedding generation, storage, and retrieval.
    """
    
    def __init__(self):
        """Initialize the embedding service"""
        try:
            self.azure_config = load_azure_config()
            self.embedding_model = AzureOpenAIEmbeddings(
                openai_api_version=self.azure_config.api_version,
                azure_deployment=self.azure_config.embedding_deployment or "text-embedding-ada-002",
                azure_endpoint=self.azure_config.endpoint,
                api_key=self.azure_config.api_key,
                chunk_size=1000  # Add the missing chunk_size parameter
            )
            self.embedding_dimension = 1536  # Default for text-embedding-ada-002
            logger.info("EmbeddingService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingService: {e}")
            raise
    
    async def create_embedding_for_entity(
        self, 
        db: Session, 
        entity: Any, 
        entity_type: str,
        force_update: bool = False
    ) -> Optional[EmbeddingStore]:
        """
        Create embedding for an entity
        
        Args:
            db: Database session
            entity: The entity to embed
            entity_type: Type of entity (e.g., 'activity', 'question')
            force_update: Whether to update existing embedding
            
        Returns:
            EmbeddingStore instance or None if failed
        """
        try:
            # Extract content and metadata
            content_text, metadata = extract_content_from_entity(entity, entity_type)
            
            if not content_text.strip():
                logger.warning(f"No content extracted for {entity_type} {entity.id}")
                return None
            
            # Check if embedding already exists
            existing_embedding = db.query(EmbeddingStore).filter(
                and_(
                    EmbeddingStore.entity_type == entity_type,
                    EmbeddingStore.entity_id == str(entity.id)
                )
            ).first()
            
            if existing_embedding and not force_update:
                logger.info(f"Embedding already exists for {entity_type} {entity.id}")
                return existing_embedding
            
            # Generate embedding
            embedding_vector = await self._generate_embedding(content_text)
            if not embedding_vector:
                logger.error(f"Failed to generate embedding for {entity_type} {entity.id}")
                return None
            
            # Create or update embedding record
            if existing_embedding:
                existing_embedding.content_text = content_text
                existing_embedding.embedding_vector = embedding_vector
                existing_embedding.embedding_metadata = metadata
                existing_embedding.updated_at = datetime.now()
                embedding_record = existing_embedding
                logger.info(f"Updated embedding for {entity_type} {entity.id}")
            else:
                embedding_record = EmbeddingStore(
                    entity_type=entity_type,
                    entity_id=str(entity.id),
                    content_text=content_text,
                    embedding_vector=embedding_vector,
                    embedding_metadata=metadata,
                    embedding_model=self.azure_config.embedding_deployment or "text-embedding-ada-002",
                    embedding_dimension=self.embedding_dimension
                )
                db.add(embedding_record)
                logger.info(f"Created embedding for {entity_type} {entity.id}")
            
            db.commit()
            return embedding_record
            
        except Exception as e:
            logger.error(f"Error creating embedding for {entity_type} {entity.id}: {e}")
            db.rollback()
            return None
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            if not text.strip():
                return None
            
            embedding = await self.embedding_model.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def search_similar_entities(
        self,
        db: Session,
        query: str,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Search for similar entities using semantic similarity
        
        Args:
            db: Database session
            query: Search query
            entity_types: List of entity types to search in
            filters: Metadata filters
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (EmbeddingStore, similarity_score) tuples
        """
        try:
            # Generate embedding for query
            query_embedding = await self._generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Build query
            db_query = db.query(EmbeddingStore)
            
            # Filter by entity types
            if entity_types:
                db_query = db_query.filter(EmbeddingStore.entity_type.in_(entity_types))
            
            # Apply metadata filters
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        # Note: This is a simplified filter. For complex JSON queries,
                        # you might need to use PostgreSQL JSON operators
                        db_query = db_query.filter(
                            EmbeddingStore.embedding_metadata.contains({key: value})
                        )
            
            # Get all embeddings
            embeddings = db_query.all()
            
            # Calculate similarities
            similarities = []
            for embedding_record in embeddings:
                similarity = self._calculate_cosine_similarity(
                    query_embedding, 
                    embedding_record.embedding_list
                )
                if similarity >= similarity_threshold:
                    similarities.append((embedding_record, similarity))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching similar entities: {e}")
            return []
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            if not vec1 or not vec2 or len(vec1) != len(vec2):
                return 0.0
            
            vec1_array = np.array(vec1)
            vec2_array = np.array(vec2)
            
            dot_product = np.dot(vec1_array, vec2_array)
            norm1 = np.linalg.norm(vec1_array)
            norm2 = np.linalg.norm(vec2_array)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    async def batch_create_embeddings(
        self,
        db: Session,
        entities: List[Tuple[Any, str]],
        batch_size: int = 10
    ) -> Dict[str, int]:
        """
        Create embeddings for multiple entities in batches
        
        Args:
            db: Database session
            entities: List of (entity, entity_type) tuples
            batch_size: Number of entities to process per batch
            
        Returns:
            Dict with success and failure counts
        """
        results = {"success": 0, "failed": 0}
        
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} of {len(entities)//batch_size + 1}")
            
            for entity, entity_type in batch:
                try:
                    embedding = await self.create_embedding_for_entity(db, entity, entity_type)
                    if embedding:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                except Exception as e:
                    logger.error(f"Error processing {entity_type} {entity.id}: {e}")
                    results["failed"] += 1
            
            # Commit batch
            try:
                db.commit()
            except Exception as e:
                logger.error(f"Error committing batch: {e}")
                db.rollback()
                results["failed"] += len(batch)
        
        logger.info(f"Batch processing completed: {results}")
        return results
    
    def get_embedding_stats(self, db: Session) -> Dict[str, Any]:
        """Get statistics about stored embeddings"""
        try:
            total_embeddings = db.query(EmbeddingStore).count()
            
            # Count by entity type
            entity_type_counts = {}
            for entity_type in db.query(EmbeddingStore.entity_type).distinct():
                count = db.query(EmbeddingStore).filter(
                    EmbeddingStore.entity_type == entity_type
                ).count()
                entity_type_counts[entity_type] = count
            
            # Get embedding models used
            models_used = db.query(EmbeddingStore.embedding_model).distinct().all()
            
            return {
                "total_embeddings": total_embeddings,
                "entity_type_counts": entity_type_counts,
                "models_used": [model for model, in models_used],
                "embedding_dimension": self.embedding_dimension
            }
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {}
    
    def delete_embedding(self, db: Session, entity_type: str, entity_id: str) -> bool:
        """Delete embedding for an entity"""
        try:
            embedding = db.query(EmbeddingStore).filter(
                and_(
                    EmbeddingStore.entity_type == entity_type,
                    EmbeddingStore.entity_id == entity_id
                )
            ).first()
            
            if embedding:
                db.delete(embedding)
                db.commit()
                logger.info(f"Deleted embedding for {entity_type} {entity_id}")
                return True
            else:
                logger.warning(f"No embedding found for {entity_type} {entity_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting embedding for {entity_type} {entity_id}: {e}")
            db.rollback()
            return False 