from typing import List, Dict, Any, Optional
from uuid import UUID
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_openai import AzureChatOpenAI
from app.core.logger import get_logger
from app.core.azure_config import load_azure_config
from app.services.vector_store import VectorStoreService
from app.models.document import Document as DocumentModel, DocumentChatSession, DocumentChatMessage
from sqlalchemy.orm import Session

logger = get_logger(__name__)

class RAGChatService:
    def __init__(self):
        self.vector_store_service = VectorStoreService()
        
        # Load Azure configuration
        try:
            azure_config = load_azure_config()
            self.llm = AzureChatOpenAI(
                openai_api_version=azure_config.api_version,
                azure_deployment=azure_config.deployment,
                azure_endpoint=azure_config.endpoint,
                api_key=azure_config.api_key,
                temperature=0.7,
                max_tokens=1000
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI: {e}")
            raise

    async def create_chat_session(
        self, 
        document_id: UUID, 
        activity_id: UUID,
        user_id: UUID, 
        session_name: Optional[str],
        db: Session
    ) -> DocumentChatSession:
        """Create a new chat session for a document in an activity"""
        
        session = DocumentChatSession(
            document_id=document_id,
            activity_id=activity_id,
            user_id=user_id,
            session_name=session_name or f"Chat Session {document_id}"
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created chat session {session.id} for document {document_id} in activity {activity_id}")
        return session

    async def get_or_create_session(
        self, 
        session_id: Optional[UUID], 
        document_id: Optional[UUID], 
        activity_id: Optional[UUID],
        user_id: UUID, 
        session_name: Optional[str],
        db: Session
    ) -> DocumentChatSession:
        """Get existing session or create new one"""
        
        if session_id:
            # Get existing session
            session = db.query(DocumentChatSession).filter(
                DocumentChatSession.id == session_id,
                DocumentChatSession.user_id == user_id
            ).first()
            
            if session:
                return session
            else:
                logger.warning(f"Session {session_id} not found or not accessible")
        
        if document_id and activity_id:
            # Create new session
            return await self.create_chat_session(document_id, activity_id, user_id, session_name, db)
        else:
            raise ValueError("Either session_id or both document_id and activity_id must be provided")

    def get_session_history(self, session_id: str, db: Session) -> BaseChatMessageHistory:
        """Get chat history for a session"""
        
        # Get messages from database
        messages = db.query(DocumentChatMessage).filter(
            DocumentChatMessage.session_id == session_id
        ).order_by(DocumentChatMessage.created_at).all()
        
        # Create LangChain chat history
        history = ChatMessageHistory()
        
        for msg in messages:
            if msg.role == "user":
                history.add_user_message(msg.content)
            elif msg.role == "assistant":
                history.add_ai_message(msg.content)
        
        return history

    async def chat_with_document(
        self, 
        message: str, 
        session_id: UUID, 
        db: Session
    ) -> Dict[str, Any]:
        """Chat with document using RAG"""
        
        # Get session
        session = db.query(DocumentChatSession).filter(
            DocumentChatSession.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get document
        document = db.query(DocumentModel).filter(
            DocumentModel.id == session.document_id
        ).first()
        
        if not document:
            raise ValueError(f"Document {session.document_id} not found")
        
        # Create retriever for this document
        retriever = self.vector_store_service.vector_store.as_retriever(
            search_kwargs={"filter": {"document_id": str(document.id)}, "k": 5}
        )
        
        # Create history-aware retriever
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm, 
            retriever, 
            contextualize_q_prompt
        )
        
        # Create answer generation chain
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        # Create conversational RAG chain with message history
        def get_session_history(session_id: str) -> BaseChatMessageHistory:
            return self.get_session_history(session_id, db)
        
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )
        
        # Generate response
        response = conversational_rag_chain.invoke(
            {"input": message},
            config={"configurable": {"session_id": str(session_id)}}
        )
        
        # Save user message
        user_message = DocumentChatMessage(
            session_id=session_id,
            role="user",
            content=message
        )
        db.add(user_message)
        
        # Save assistant message
        assistant_message = DocumentChatMessage(
            session_id=session_id,
            role="assistant",
            content=response['answer'],
            message_metadata={"sources": response.get('context', [])}
        )
        db.add(assistant_message)
        
        # Update session timestamp
        session.updated_at = db.query(DocumentChatMessage).filter(
            DocumentChatMessage.session_id == session_id
        ).order_by(DocumentChatMessage.created_at.desc()).first().created_at
        
        db.commit()
        
        # Extract sources from response
        sources = []
        if 'context' in response:
            for doc in response['context']:
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })
        
        return {
            "message": response['answer'],
            "session_id": session_id,
            "sources": sources,
            "metadata": {
                "document_name": document.name,
                "document_type": document.document_type.value,
                "activity_id": str(session.activity_id)
            }
        }

    async def chat_with_activity_documents(
        self, 
        message: str, 
        activity_id: UUID, 
        user_id: UUID,
        session_name: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """Chat with all documents in an activity using RAG"""
        
        # Get all documents for the activity
        documents = db.query(DocumentModel).filter(
            DocumentModel.activity_id == activity_id,
            DocumentModel.is_processed == True
        ).all()
        
        if not documents:
            raise ValueError(f"No processed documents found for activity {activity_id}")
        
        # Create retriever for all documents in the activity
        retriever = self.vector_store_service.vector_store.as_retriever(
            search_kwargs={"filter": {"activity_id": str(activity_id)}, "k": 8}
        )
        
        # Create history-aware retriever
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm, 
            retriever, 
            contextualize_q_prompt
        )
        
        # Create answer generation chain
        system_prompt = (
            "You are an assistant for question-answering tasks based on activity documents. "
            "Use the following pieces of retrieved context from the activity documents to answer "
            "the question. If you don't know the answer, say that you don't know. "
            "Keep the answer concise and relevant to the activity context."
            "\n\n"
            "{context}"
        )
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        # For activity-level chat, we'll use a simple approach without persistent sessions
        # Generate response
        response = rag_chain.invoke({"input": message})
        
        # Extract sources from response
        sources = []
        if 'context' in response:
            for doc in response['context']:
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })
        
        return {
            "message": response['answer'],
            "session_id": None,  # No persistent session for activity-level chat
            "sources": sources,
            "metadata": {
                "activity_id": str(activity_id),
                "document_count": len(documents)
            }
        }

    async def get_chat_history(
        self, 
        session_id: UUID, 
        db: Session
    ) -> List[DocumentChatMessage]:
        """Get chat history for a session"""
        
        messages = db.query(DocumentChatMessage).filter(
            DocumentChatMessage.session_id == session_id
        ).order_by(DocumentChatMessage.created_at).all()
        
        return messages

    async def delete_chat_session(self, session_id: UUID, db: Session) -> bool:
        """Delete a chat session and all its messages"""
        
        try:
            # Delete all messages in the session
            db.query(DocumentChatMessage).filter(
                DocumentChatMessage.session_id == session_id
            ).delete()
            
            # Delete the session
            db.query(DocumentChatSession).filter(
                DocumentChatSession.id == session_id
            ).delete()
            
            db.commit()
            
            logger.info(f"Deleted chat session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {e}")
            db.rollback()
            return False 