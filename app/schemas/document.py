from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    URL = "url"
    MARKDOWN = "markdown"

class DocumentBase(BaseModel):
    name: str = Field(..., description="Document name")
    description: Optional[str] = Field(None, description="Document description")
    document_type: DocumentType = Field(..., description="Document type")
    tags: Optional[List[str]] = Field(None, description="Document tags")

class DocumentCreate(DocumentBase):
    activity_id: UUID = Field(..., description="Activity ID")

class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class DocumentResponse(DocumentBase):
    id: UUID
    activity_id: UUID
    uploaded_by: UUID
    file_path: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None
    is_processed: bool
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentChatSessionBase(BaseModel):
    session_name: Optional[str] = Field(None, description="Session name")

class DocumentChatSessionCreate(DocumentChatSessionBase):
    document_id: UUID = Field(..., description="Document ID")
    activity_id: UUID = Field(..., description="Activity ID")

class DocumentChatSessionResponse(DocumentChatSessionBase):
    id: UUID
    document_id: UUID
    activity_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentChatMessageBase(BaseModel):
    content: str = Field(..., description="Message content")

class DocumentChatMessageCreate(DocumentChatMessageBase):
    role: str = Field(..., description="Message role (user/assistant)")

class DocumentChatMessageResponse(DocumentChatMessageBase):
    id: UUID
    session_id: UUID
    role: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class DocumentChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[UUID] = Field(None, description="Existing session ID")
    document_id: Optional[UUID] = Field(None, description="Document ID for new session")
    activity_id: Optional[UUID] = Field(None, description="Activity ID for new session")

class DocumentChatResponse(BaseModel):
    message: str = Field(..., description="Assistant response")
    session_id: UUID = Field(..., description="Session ID")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="Source documents used")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class DocumentUploadResponse(BaseModel):
    document_id: UUID = Field(..., description="Uploaded document ID")
    activity_id: UUID = Field(..., description="Activity ID")
    message: str = Field(..., description="Upload status message")
    processing_status: str = Field(..., description="Processing status") 