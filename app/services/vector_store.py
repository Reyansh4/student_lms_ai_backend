import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from app.core.logger import get_logger
from app.models.document import Document as DocumentModel
from sqlalchemy.orm import Session

logger = get_logger(__name__)

class VectorStoreService:
    def __init__(self):
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Create vector store directory
        self.vector_store_dir = Path("vector_store")
        self.vector_store_dir.mkdir(exist_ok=True)
        
        # Initialize Chroma vector store
        self.vector_store = Chroma(
            persist_directory=str(self.vector_store_dir),
            embedding_function=self.embeddings
        )

    async def add_document_to_vector_store(
        self, 
        document: DocumentModel, 
        chunks: List[Document]
    ) -> bool:
        """Add document chunks to vector store"""
        try:
            # Add metadata to chunks
            for chunk in chunks:
                chunk.metadata.update({
                    "document_id": str(document.id),
                    "document_name": document.name,
                    "document_type": document.document_type.value,
                    "activity_id": str(document.activity_id),
                    "uploaded_by": str(document.uploaded_by)
                })
            
            # Add to vector store
            self.vector_store.add_documents(chunks)
            self.vector_store.persist()
            
            logger.info(f"Added {len(chunks)} chunks from document {document.id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document {document.id} to vector store: {e}")
            return False

    async def search_similar_chunks(
        self, 
        query: str, 
        activity_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        k: int = 5
    ) -> List[Document]:
        """Search for similar chunks in vector store"""
        try:
            # Build filter
            filter_dict = {}
            if activity_id:
                filter_dict["activity_id"] = activity_id
            if document_ids:
                filter_dict["document_id"] = {"$in": document_ids}
            
            # If no filters, set to None
            if not filter_dict:
                filter_dict = None
            
            # Search vector store
            results = self.vector_store.similarity_search(
                query, 
                k=k,
                filter=filter_dict
            )
            
            logger.info(f"Found {len(results)} similar chunks for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    async def search_with_score(
        self, 
        query: str, 
        activity_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        k: int = 5
    ) -> List[tuple[Document, float]]:
        """Search for similar chunks with similarity scores"""
        try:
            # Build filter
            filter_dict = {}
            if activity_id:
                filter_dict["activity_id"] = activity_id
            if document_ids:
                filter_dict["document_id"] = {"$in": document_ids}
            
            # If no filters, set to None
            if not filter_dict:
                filter_dict = None
            
            # Search vector store with scores
            results = self.vector_store.similarity_search_with_score(
                query, 
                k=k,
                filter=filter_dict
            )
            
            logger.info(f"Found {len(results)} similar chunks with scores for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store with scores: {e}")
            return []

    async def delete_document_from_vector_store(self, document_id: str) -> bool:
        """Delete document chunks from vector store"""
        try:
            # Get collection
            collection = self.vector_store._collection
            
            # Delete documents with matching document_id
            collection.delete(where={"document_id": document_id})
            
            logger.info(f"Deleted document {document_id} from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from vector store: {e}")
            return False

    async def get_document_chunks_from_vector_store(self, document_id: str) -> List[Document]:
        """Get all chunks for a specific document from vector store"""
        try:
            # Search for all chunks of the document
            results = self.vector_store.similarity_search(
                "",  # Empty query to get all documents
                k=1000,  # Large number to get all chunks
                filter={"document_id": document_id}
            )
            
            logger.info(f"Retrieved {len(results)} chunks for document {document_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving chunks for document {document_id}: {e}")
            return []

    async def get_activity_chunks_from_vector_store(self, activity_id: str) -> List[Document]:
        """Get all chunks for a specific activity from vector store"""
        try:
            # Search for all chunks of the activity
            results = self.vector_store.similarity_search(
                "",  # Empty query to get all documents
                k=1000,  # Large number to get all chunks
                filter={"activity_id": activity_id}
            )
            
            logger.info(f"Retrieved {len(results)} chunks for activity {activity_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving chunks for activity {activity_id}: {e}")
            return []

    async def update_document_in_vector_store(
        self, 
        document: DocumentModel, 
        chunks: List[Document]
    ) -> bool:
        """Update document in vector store (delete old, add new)"""
        try:
            # Delete old chunks
            await self.delete_document_from_vector_store(str(document.id))
            
            # Add new chunks
            success = await self.add_document_to_vector_store(document, chunks)
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating document {document.id} in vector store: {e}")
            return False

    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            collection = self.vector_store._collection
            count = collection.count()
            
            return {
                "total_chunks": count,
                "vector_store_path": str(self.vector_store_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return {"error": str(e)} 