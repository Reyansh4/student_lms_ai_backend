"""
API routes for embedding system
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.embeddings.service import EmbeddingService
from app.embeddings.retrievers import SemanticRetriever
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str
    entity_types: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 10
    similarity_threshold: float = 0.7

class SearchResponse(BaseModel):
    entity_type: str
    entity_id: str
    content_text: str
    similarity_score: float
    metadata: Dict[str, Any]
    created_at: Optional[str]

class EmbeddingStatsResponse(BaseModel):
    total_embeddings: int
    entity_type_counts: Dict[str, int]
    models_used: List[str]
    embedding_dimension: int

class BatchCreateRequest(BaseModel):
    entity_type: str
    entity_ids: List[str]

# Initialize services
embedding_service = EmbeddingService()
semantic_retriever = SemanticRetriever()

@router.post("/search", response_model=List[SearchResponse])
async def search_embeddings(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search for entities using semantic similarity
    """
    try:
        results = await embedding_service.search_similar_entities(
            db=db,
            query=request.query,
            entity_types=request.entity_types,
            filters=request.filters,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        return semantic_retriever.format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error in embedding search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/search/activities", response_model=List[SearchResponse])
async def search_activities(
    query: str = Query(..., description="Search query"),
    difficulty_level: Optional[str] = Query(None, description="Filter by difficulty level"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    access_type: Optional[str] = Query(None, description="Filter by access type"),
    ai_guide_only: bool = Query(False, description="Only return activities with AI guide"),
    top_k: int = Query(10, ge=1, le=50),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search for activities with semantic similarity
    """
    try:
        results = await semantic_retriever.search_activities(
            db=db,
            query=query,
            difficulty_level=difficulty_level,
            category_id=category_id,
            access_type=access_type,
            ai_guide_only=ai_guide_only,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        return semantic_retriever.format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error in activity search: {e}")
        raise HTTPException(status_code=500, detail="Activity search failed")

@router.get("/search/questions", response_model=List[SearchResponse])
async def search_questions(
    query: str = Query(..., description="Search query"),
    activity_id: Optional[str] = Query(None, description="Filter by activity ID"),
    has_solution: Optional[bool] = Query(None, description="Filter by solution availability"),
    has_answer: Optional[bool] = Query(None, description="Filter by answer availability"),
    top_k: int = Query(10, ge=1, le=50),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search for questions with semantic similarity
    """
    try:
        results = await semantic_retriever.search_questions(
            db=db,
            query=query,
            activity_id=activity_id,
            has_solution=has_solution,
            has_answer=has_answer,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        return semantic_retriever.format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error in question search: {e}")
        raise HTTPException(status_code=500, detail="Question search failed")

@router.get("/search/ai-responses", response_model=List[SearchResponse])
async def search_ai_responses(
    query: str = Query(..., description="Search query"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    question_id: Optional[str] = Query(None, description="Filter by question ID"),
    top_k: int = Query(10, ge=1, le=50),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search for AI responses with semantic similarity
    """
    try:
        results = await semantic_retriever.search_ai_responses(
            db=db,
            query=query,
            session_id=session_id,
            user_id=user_id,
            question_id=question_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        return semantic_retriever.format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error in AI response search: {e}")
        raise HTTPException(status_code=500, detail="AI response search failed")

@router.get("/recommendations", response_model=List[SearchResponse])
async def get_recommendations(
    query: str = Query(..., description="Recommendation query"),
    entity_types: Optional[List[str]] = Query(None, description="Entity types to search"),
    top_k: int = Query(10, ge=1, le=50),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get personalized recommendations for the current user
    """
    try:
        results = await semantic_retriever.get_recommendations_for_user(
            db=db,
            user_id=str(current_user.id),
            query=query,
            entity_types=entity_types,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        return semantic_retriever.format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.get("/similar-activities/{activity_id}", response_model=List[SearchResponse])
async def get_similar_activities(
    activity_id: str,
    top_k: int = Query(5, ge=1, le=20),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Find activities similar to a given activity
    """
    try:
        results = await semantic_retriever.get_similar_activities(
            db=db,
            activity_id=activity_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        return semantic_retriever.format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error finding similar activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar activities")

@router.get("/stats", response_model=EmbeddingStatsResponse)
async def get_embedding_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get statistics about stored embeddings
    """
    try:
        stats = embedding_service.get_embedding_stats(db)
        return EmbeddingStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get embedding stats")

@router.post("/create/{entity_type}/{entity_id}")
async def create_embedding(
    entity_type: str,
    entity_id: str,
    force_update: bool = Query(False, description="Force update existing embedding"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create embedding for a specific entity
    """
    try:
        # This would need to fetch the actual entity from the database
        # For now, we'll return a placeholder response
        logger.info(f"Creating embedding for {entity_type} {entity_id}")
        
        # TODO: Implement actual entity fetching and embedding creation
        # entity = get_entity_by_type_and_id(db, entity_type, entity_id)
        # embedding = await embedding_service.create_embedding_for_entity(
        #     db, entity, entity_type, force_update
        # )
        
        return {
            "message": f"Embedding creation initiated for {entity_type} {entity_id}",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "force_update": force_update
        }
        
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to create embedding")

@router.delete("/{entity_type}/{entity_id}")
async def delete_embedding(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete embedding for a specific entity
    """
    try:
        success = embedding_service.delete_embedding(db, entity_type, entity_id)
        
        if success:
            return {"message": f"Embedding deleted for {entity_type} {entity_id}"}
        else:
            raise HTTPException(status_code=404, detail="Embedding not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete embedding")

@router.post("/batch-create")
async def batch_create_embeddings(
    request: BatchCreateRequest,
    batch_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create embeddings for multiple entities in batches
    """
    try:
        logger.info(f"Batch creating embeddings for {len(request.entity_ids)} {request.entity_type} entities")
        
        # TODO: Implement actual batch creation
        # entities = get_entities_by_type_and_ids(db, request.entity_type, request.entity_ids)
        # results = await embedding_service.batch_create_embeddings(
        #     db, [(entity, request.entity_type) for entity in entities], batch_size
        # )
        
        return {
            "message": f"Batch embedding creation initiated for {len(request.entity_ids)} {request.entity_type} entities",
            "entity_type": request.entity_type,
            "entity_count": len(request.entity_ids),
            "batch_size": batch_size
        }
        
    except Exception as e:
        logger.error(f"Error in batch embedding creation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create batch embeddings") 