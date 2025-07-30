"""
Semantic retrievers for different use cases
"""

from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.embeddings.service import EmbeddingService
from app.embeddings.models import EmbeddingStore
from app.core.logger import get_logger

logger = get_logger(__name__)

class SemanticRetriever:
    """
    Advanced semantic retriever with filtering and ranking capabilities
    """
    
    def __init__(self):
        """Initialize the semantic retriever"""
        self.embedding_service = EmbeddingService()
    
    async def search_activities(
        self,
        db: Session,
        query: str,
        difficulty_level: Optional[str] = None,
        category_id: Optional[str] = None,
        access_type: Optional[str] = None,
        ai_guide_only: bool = False,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Search for activities with semantic similarity and filtering
        
        Args:
            db: Database session
            query: Search query
            difficulty_level: Filter by difficulty level
            category_id: Filter by category ID
            access_type: Filter by access type
            ai_guide_only: Only return activities with AI guide
            top_k: Number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (EmbeddingStore, similarity_score) tuples
        """
        filters = {}
        if difficulty_level:
            filters["difficulty_level"] = difficulty_level
        if category_id:
            filters["category_id"] = category_id
        if access_type:
            filters["access_type"] = access_type
        if ai_guide_only:
            filters["ai_guide"] = True
        
        return await self.embedding_service.search_similar_entities(
            db=db,
            query=query,
            entity_types=["activity"],
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
    
    async def search_questions(
        self,
        db: Session,
        query: str,
        activity_id: Optional[str] = None,
        has_solution: Optional[bool] = None,
        has_answer: Optional[bool] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Search for questions with semantic similarity and filtering
        """
        filters = {}
        if activity_id:
            filters["activity_id"] = activity_id
        if has_solution is not None:
            filters["has_solution"] = has_solution
        if has_answer is not None:
            filters["has_answer"] = has_answer
        
        return await self.embedding_service.search_similar_entities(
            db=db,
            query=query,
            entity_types=["activity_question"],
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
    
    async def search_ai_responses(
        self,
        db: Session,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        question_id: Optional[str] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Search for AI responses with semantic similarity and filtering
        """
        filters = {}
        if session_id:
            filters["session_id"] = session_id
        if user_id:
            filters["user_id"] = user_id
        if question_id:
            filters["question_id"] = question_id
        
        return await self.embedding_service.search_similar_entities(
            db=db,
            query=query,
            entity_types=["activity_ai_response"],
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
    
    async def search_sessions(
        self,
        db: Session,
        query: str,
        activity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        has_feedback: Optional[bool] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Search for sessions with semantic similarity and filtering
        """
        filters = {}
        if activity_id:
            filters["activity_id"] = activity_id
        if user_id:
            filters["user_id"] = user_id
        if status:
            filters["status"] = status
        if has_feedback is not None:
            filters["has_feedback"] = has_feedback
        
        return await self.embedding_service.search_similar_entities(
            db=db,
            query=query,
            entity_types=["activity_session"],
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
    
    async def search_documents(
        self,
        db: Session,
        query: str,
        activity_id: Optional[str] = None,
        file_type: Optional[str] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Search for documents with semantic similarity and filtering
        """
        filters = {}
        if activity_id:
            filters["activity_id"] = activity_id
        if file_type:
            filters["file_type"] = file_type
        
        return await self.embedding_service.search_similar_entities(
            db=db,
            query=query,
            entity_types=["activity_document"],
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
    
    async def search_templates(
        self,
        db: Session,
        query: str,
        difficulty_level: Optional[str] = None,
        category_id: Optional[str] = None,
        access_type: Optional[str] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Search for templates with semantic similarity and filtering
        """
        filters = {}
        if difficulty_level:
            filters["difficulty_level"] = difficulty_level
        if category_id:
            filters["category_id"] = category_id
        if access_type:
            filters["access_type"] = access_type
        
        return await self.embedding_service.search_similar_entities(
            db=db,
            query=query,
            entity_types=["activity_template"],
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
    
    async def search_users(
        self,
        db: Session,
        query: str,
        is_active: Optional[bool] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Search for users with semantic similarity and filtering
        """
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        if city:
            filters["city"] = city
        if country:
            filters["country"] = country
        
        return await self.embedding_service.search_similar_entities(
            db=db,
            query=query,
            entity_types=["user"],
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
    
    async def cross_entity_search(
        self,
        db: Session,
        query: str,
        entity_types: List[str],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Search across multiple entity types with unified ranking
        """
        return await self.embedding_service.search_similar_entities(
            db=db,
            query=query,
            entity_types=entity_types,
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
    
    async def get_recommendations_for_user(
        self,
        db: Session,
        user_id: str,
        query: str,
        entity_types: Optional[List[str]] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Get personalized recommendations for a user
        """
        if entity_types is None:
            entity_types = ["activity", "activity_template"]
        
        # Add user-specific filters
        filters = {
            "access_type": "global"  # Start with global content
        }
        
        return await self.embedding_service.search_similar_entities(
            db=db,
            query=query,
            entity_types=entity_types,
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
    
    async def get_similar_activities(
        self,
        db: Session,
        activity_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EmbeddingStore, float]]:
        """
        Find activities similar to a given activity
        """
        # Get the activity's embedding
        activity_embedding = db.query(EmbeddingStore).filter(
            EmbeddingStore.entity_type == "activity",
            EmbeddingStore.entity_id == activity_id
        ).first()
        
        if not activity_embedding:
            logger.warning(f"No embedding found for activity {activity_id}")
            return []
        
        # Search for similar activities (excluding the original)
        similar_activities = await self.embedding_service.search_similar_entities(
            db=db,
            query=activity_embedding.content_text,
            entity_types=["activity"],
            top_k=top_k + 1,  # Get one extra to account for exclusion
            similarity_threshold=similarity_threshold
        )
        
        # Filter out the original activity
        filtered_results = [
            (embedding, score) for embedding, score in similar_activities
            if embedding.entity_id != activity_id
        ]
        
        return filtered_results[:top_k]
    
    def format_search_results(
        self,
        results: List[Tuple[EmbeddingStore, float]]
    ) -> List[Dict[str, Any]]:
        """
        Format search results for API response
        """
        formatted_results = []
        
        for embedding, similarity in results:
            result = {
                "entity_type": embedding.entity_type,
                "entity_id": embedding.entity_id,
                "content_text": embedding.content_text,
                "similarity_score": round(similarity, 4),
                "metadata": embedding.metadata,
                "created_at": embedding.created_at.isoformat() if embedding.created_at else None
            }
            formatted_results.append(result)
        
        return formatted_results 