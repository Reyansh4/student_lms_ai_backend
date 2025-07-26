import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy import create_engine, text, Column, String, DateTime, ForeignKey, JSON, UUID, Text, Boolean, Integer, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.logger import get_logger
from app.models.document import Document as DocumentModel
from app.core.config import settings
import uuid
from datetime import datetime

logger = get_logger(__name__)

# Create base for pgvector models
PgVectorBase = declarative_base()

class DocumentChunk(PgVectorBase):
    """Model for storing document chunks with embeddings in PostgreSQL"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activity.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Text, nullable=True)  # Temporarily using Text instead of VECTOR
    meta_data = Column(JSON, nullable=True)  # Renamed from metadata to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"

class EvaluationEmbedding(PgVectorBase):
    """Model for storing evaluation-related embeddings"""
    __tablename__ = "evaluation_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_results.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activity.id"), nullable=False)
    content_type = Column(String(50), nullable=False)  # 'quiz_response', 'chat_message', 'document_understanding'
    content_text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # Temporarily using Text instead of VECTOR
    meta_data = Column(JSON, nullable=True)  # Renamed from metadata to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<EvaluationEmbedding(id={self.id}, content_type={self.content_type})>"

class PgVectorService:
    def __init__(self):
        """Initialize pgvector service with PostgreSQL connection"""
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Ensure pgvector extension is enabled
        self._ensure_pgvector_extension()
        
        # Create tables
        PgVectorBase.metadata.create_all(bind=self.engine)
        
        logger.info("PgVector service initialized successfully")
    
    def _ensure_pgvector_extension(self):
        """Ensure pgvector extension is enabled in PostgreSQL"""
        try:
            with self.engine.connect() as conn:
                # Check if extension exists
                result = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
                if not result.fetchone():
                    # Create extension
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                    logger.info("pgvector extension created successfully")
                else:
                    logger.info("pgvector extension already exists")
        except Exception as e:
            logger.error(f"Error ensuring pgvector extension: {e}")
            raise
    
    async def add_document_chunks(
        self, 
        document: DocumentModel, 
        chunks: List[Document]
    ) -> bool:
        """Add document chunks with embeddings to PostgreSQL"""
        try:
            db = self.SessionLocal()
            
            for i, chunk in enumerate(chunks):
                # Generate embedding for chunk
                embedding = self.embeddings.embed_query(chunk.page_content)
                
                # Create document chunk record
                doc_chunk = DocumentChunk(
                    document_id=document.id,
                    activity_id=document.activity_id,
                    chunk_text=chunk.page_content,
                    chunk_index=i,
                    embedding=embedding,
                    meta_data=chunk.metadata
                )
                
                db.add(doc_chunk)
            
            db.commit()
            logger.info(f"Added {len(chunks)} chunks with embeddings for document {document.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document chunks to pgvector: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    async def search_similar_chunks(
        self, 
        query: str, 
        activity_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        k: int = 5
    ) -> List[Document]:
        """Search for similar chunks using vector similarity"""
        try:
            db = self.SessionLocal()
            
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Build SQL query with filters
            sql = """
            SELECT 
                dc.id,
                dc.chunk_text,
                dc.chunk_index,
                dc.meta_data,
                dc.embedding <=> :query_embedding as distance
            FROM document_chunks dc
            WHERE 1=1
            """
            
            params = {"query_embedding": query_embedding}
            
            if activity_id:
                sql += " AND dc.activity_id = :activity_id"
                params["activity_id"] = activity_id
            
            if document_ids:
                sql += " AND dc.document_id = ANY(:document_ids)"
                params["document_ids"] = document_ids
            
            sql += " ORDER BY distance ASC LIMIT :k"
            params["k"] = k
            
            # Execute query
            result = db.execute(text(sql), params)
            rows = result.fetchall()
            
            # Convert to Document objects
            documents = []
            for row in rows:
                doc = Document(
                    page_content=row.chunk_text,
                    metadata={
                        "id": str(row.id),
                        "chunk_index": row.chunk_index,
                        "distance": float(row.distance),
                        **row.meta_data
                    }
                )
                documents.append(doc)
            
            logger.info(f"Found {len(documents)} similar chunks for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching pgvector: {e}")
            return []
        finally:
            if db:
                db.close()
    
    async def search_with_score(
        self, 
        query: str, 
        activity_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        k: int = 5
    ) -> List[Tuple[Document, float]]:
        """Search for similar chunks with similarity scores"""
        try:
            db = self.SessionLocal()
            
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Build SQL query with filters
            sql = """
            SELECT 
                dc.id,
                dc.chunk_text,
                dc.chunk_index,
                dc.meta_data,
                dc.embedding <=> :query_embedding as distance
            FROM document_chunks dc
            WHERE 1=1
            """
            
            params = {"query_embedding": query_embedding}
            
            if activity_id:
                sql += " AND dc.activity_id = :activity_id"
                params["activity_id"] = activity_id
            
            if document_ids:
                sql += " AND dc.document_id = ANY(:document_ids)"
                params["document_ids"] = document_ids
            
            sql += " ORDER BY distance ASC LIMIT :k"
            params["k"] = k
            
            # Execute query
            result = db.execute(text(sql), params)
            rows = result.fetchall()
            
            # Convert to Document objects with scores
            results = []
            for row in rows:
                doc = Document(
                    page_content=row.chunk_text,
                    metadata={
                        "id": str(row.id),
                        "chunk_index": row.chunk_index,
                        **row.meta_data
                    }
                )
                score = 1.0 - float(row.distance)  # Convert distance to similarity score
                results.append((doc, score))
            
            logger.info(f"Found {len(results)} similar chunks with scores for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching pgvector with scores: {e}")
            return []
        finally:
            if db:
                db.close()
    
    async def add_evaluation_embedding(
        self,
        evaluation_id: str,
        user_id: str,
        activity_id: str,
        content_type: str,
        content_text: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Add evaluation-related content with embedding"""
        try:
            db = self.SessionLocal()
            
            # Generate embedding for content
            embedding = self.embeddings.embed_query(content_text)
            
            # Create evaluation embedding record
            eval_embedding = EvaluationEmbedding(
                evaluation_id=evaluation_id,
                user_id=user_id,
                activity_id=activity_id,
                content_type=content_type,
                content_text=content_text,
                embedding=embedding,
                meta_data=metadata
            )
            
            db.add(eval_embedding)
            db.commit()
            
            logger.info(f"Added evaluation embedding for {content_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding evaluation embedding: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    async def search_evaluation_similarities(
        self,
        query: str,
        user_id: str,
        activity_id: str,
        content_type: Optional[str] = None,
        k: int = 5
    ) -> List[Tuple[str, float]]:
        """Search for similar evaluation content"""
        try:
            db = self.SessionLocal()
            
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Build SQL query
            sql = """
            SELECT 
                ee.content_text,
                ee.embedding <=> :query_embedding as distance
            FROM evaluation_embeddings ee
            WHERE ee.user_id = :user_id 
            AND ee.activity_id = :activity_id
            """
            
            params = {
                "query_embedding": query_embedding,
                "user_id": user_id,
                "activity_id": activity_id
            }
            
            if content_type:
                sql += " AND ee.content_type = :content_type"
                params["content_type"] = content_type
            
            sql += " ORDER BY distance ASC LIMIT :k"
            params["k"] = k
            
            # Execute query
            result = db.execute(text(sql), params)
            rows = result.fetchall()
            
            # Convert to results
            results = []
            for row in rows:
                score = 1.0 - float(row.distance)
                results.append((row.content_text, score))
            
            logger.info(f"Found {len(results)} similar evaluation content for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching evaluation similarities: {e}")
            return []
        finally:
            if db:
                db.close()
    
    async def delete_document_chunks(self, document_id: str) -> bool:
        """Delete document chunks from pgvector"""
        try:
            db = self.SessionLocal()
            
            # Delete chunks for document
            result = db.execute(
                text("DELETE FROM document_chunks WHERE document_id = :document_id"),
                {"document_id": document_id}
            )
            
            db.commit()
            deleted_count = result.rowcount
            
            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get pgvector statistics"""
        try:
            db = self.SessionLocal()
            
            # Get chunk count
            chunk_count = db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
            
            # Get evaluation embedding count
            eval_count = db.execute(text("SELECT COUNT(*) FROM evaluation_embeddings")).scalar()
            
            return {
                "total_chunks": chunk_count,
                "total_evaluation_embeddings": eval_count,
                "vector_store_type": "pgvector"
            }
            
        except Exception as e:
            logger.error(f"Error getting pgvector stats: {e}")
            return {"error": str(e)}
        finally:
            if db:
                db.close() 