import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiofiles
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.core.logger import get_logger
from app.models.document import Document as DocumentModel, DocumentType
from sqlalchemy.orm import Session

logger = get_logger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Create upload directory if it doesn't exist
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)

    async def process_uploaded_file(
        self, 
        file_content: bytes, 
        filename: str, 
        mime_type: str,
        activity_id: str,
        uploaded_by: str,
        db: Session
    ) -> DocumentModel:
        """Process an uploaded file and create a document record for an activity"""
        
        # Determine document type
        document_type = self._get_document_type(filename, mime_type)
        
        # Save file temporarily
        file_path = self.upload_dir / filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # Create document record
        document = DocumentModel(
            activity_id=activity_id,
            uploaded_by=uploaded_by,
            name=filename,
            document_type=document_type,
            file_path=str(file_path),
            file_size=len(file_content),
            mime_type=mime_type,
            is_processed=False
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document content
        try:
            await self._process_document_content(document, db)
            document.is_processed = True
            db.commit()
            logger.info(f"Document {document.id} processed successfully")
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {e}")
            document.is_processed = False
            db.commit()
            raise
        
        return document

    def _get_document_type(self, filename: str, mime_type: str) -> DocumentType:
        """Determine document type from filename and MIME type"""
        extension = Path(filename).suffix.lower()
        
        if extension == '.pdf' or mime_type == 'application/pdf':
            return DocumentType.PDF
        elif extension == '.docx' or mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return DocumentType.DOCX
        elif extension == '.txt' or mime_type == 'text/plain':
            return DocumentType.TXT
        elif extension == '.csv' or mime_type == 'text/csv':
            return DocumentType.CSV
        elif extension == '.json' or mime_type == 'application/json':
            return DocumentType.JSON
        elif extension == '.md' or mime_type == 'text/markdown':
            return DocumentType.MARKDOWN
        else:
            return DocumentType.TXT  # Default to text

    async def _process_document_content(self, document: DocumentModel, db: Session):
        """Extract and process document content"""
        
        if document.document_type == DocumentType.PDF:
            loader = PyPDFLoader(document.file_path)
        elif document.document_type == DocumentType.TXT:
            loader = TextLoader(document.file_path)
        elif document.document_type == DocumentType.CSV:
            loader = CSVLoader(document.file_path)
        else:
            # For other types, try text loader
            loader = TextLoader(document.file_path)
        
        # Load documents
        documents = loader.load()
        
        # Extract full content
        full_content = "\n".join([doc.page_content for doc in documents])
        document.content = full_content
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Store chunks as JSON
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_data.append({
                "id": i,
                "content": chunk.page_content,
                "metadata": chunk.metadata
            })
        
        document.chunks = chunk_data
        db.commit()

    async def process_url_document(
        self, 
        url: str, 
        name: str, 
        description: Optional[str],
        activity_id: str,
        uploaded_by: str,
        db: Session
    ) -> DocumentModel:
        """Process a document from URL for an activity"""
        
        document = DocumentModel(
            activity_id=activity_id,
            uploaded_by=uploaded_by,
            name=name,
            description=description,
            document_type=DocumentType.URL,
            url=url,
            is_processed=False
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # TODO: Implement URL content extraction
        # For now, mark as processed
        document.is_processed = True
        db.commit()
        
        return document

    def get_document_chunks(self, document: DocumentModel) -> List[Document]:
        """Get document chunks as LangChain Document objects"""
        if not document.chunks:
            return []
        
        chunks = []
        for chunk_data in document.chunks:
            doc = Document(
                page_content=chunk_data["content"],
                metadata=chunk_data.get("metadata", {})
            )
            chunks.append(doc)
        
        return chunks

    async def delete_document(self, document: DocumentModel, db: Session):
        """Delete document and its associated file"""
        
        # Delete file if it exists
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        logger.info(f"Document {document.id} deleted successfully") 