from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, UUID, Text, Boolean, Integer, func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
import enum

class DocumentType(enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    URL = "url"
    MARKDOWN = "markdown"

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=False)
    uploaded_by = Column(UUID, ForeignKey("users.id"), nullable=False)  # Who uploaded the document
    name = Column(String(200), nullable=False)
    description = Column(Text)
    document_type = Column(Enum(DocumentType), nullable=False)
    file_path = Column(String(500))
    url = Column(String(500))
    content = Column(Text)
    is_processed = Column(Boolean, default=False)
    embeddings = Column(JSON)  # Store document embeddings
    chunks = Column(JSON)  # Store document chunks
    file_size = Column(Integer)
    mime_type = Column(String(100))
    tags = Column(JSON)  # Store tags for categorization
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime)

    # Relationships
    activity = relationship("Activity", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents", foreign_keys=[uploaded_by])
    chat_sessions = relationship("DocumentChatSession", back_populates="document")

class DocumentChatSession(Base):
    __tablename__ = "document_chat_sessions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID, ForeignKey("documents.id"), nullable=False)
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    session_name = Column(String(200))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    document = relationship("Document", back_populates="chat_sessions")
    activity = relationship("Activity", back_populates="document_chat_sessions")
    user = relationship("User", back_populates="document_chat_sessions")
    messages = relationship("DocumentChatMessage", back_populates="session")

class DocumentChatMessage(Base):
    __tablename__ = "document_chat_messages"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID, ForeignKey("document_chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    message_metadata = Column(JSON)  # Store additional metadata like sources used

    # Relationships
    session = relationship("DocumentChatSession", back_populates="messages") 