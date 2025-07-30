"""
Content extractors for different model types
"""

from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from app.models.activity import Activity
from app.models.activity_question import ActivityQuestion
from app.models.activity_ai_response import ActivityAIResponse
from app.models.activity_session import ActivitySession
from app.models.activity_document import ActivityDocument
from app.models.activity_templates import ActivityTemplate
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)

class ContentExtractor(ABC):
    """Abstract base class for content extractors"""
    
    @abstractmethod
    def extract_content(self, entity: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Extract content text and metadata from entity
        
        Returns:
            Tuple[str, Dict[str, Any]]: (content_text, metadata)
        """
        pass

class ActivityExtractor(ContentExtractor):
    """Extract content from Activity model"""
    
    def extract_content(self, activity: Activity) -> Tuple[str, Dict[str, Any]]:
        """Extract content from Activity"""
        content_parts = []
        
        # Main content
        if activity.name:
            content_parts.append(f"Activity: {activity.name}")
        if activity.description:
            content_parts.append(f"Description: {activity.description}")
        if activity.final_description:
            content_parts.append(f"Final Description: {activity.final_description}")
        
        # Combine all content
        content_text = "\n".join(content_parts)
        
        # Rich metadata
        metadata = {
            "entity_type": "activity",
            "entity_id": str(activity.id),
            "name": activity.name,
            "difficulty_level": activity.difficulty_level.value if activity.difficulty_level else None,
            "access_type": activity.access_type.value if activity.access_type else None,
            "category_id": str(activity.category_id) if activity.category_id else None,
            "sub_category_id": str(activity.sub_category_id) if activity.sub_category_id else None,
            "ai_guide": activity.ai_guide,
            "is_active": activity.is_active,
            "created_by": str(activity.created_by) if activity.created_by else None,
            "created_at": activity.created_at.isoformat() if activity.created_at else None,
            "has_clarification_questions": bool(activity.clarification_questions),
            "content_length": len(content_text)
        }
        
        return content_text, metadata

class ActivityQuestionExtractor(ContentExtractor):
    """Extract content from ActivityQuestion model"""
    
    def extract_content(self, question: ActivityQuestion) -> Tuple[str, Dict[str, Any]]:
        """Extract content from ActivityQuestion"""
        content_parts = []
        
        # Question content
        if question.question_text:
            content_parts.append(f"Question: {question.question_text}")
        if question.solution_steps:
            content_parts.append(f"Solution Steps: {question.solution_steps}")
        if question.answer:
            content_parts.append(f"Answer: {question.answer}")
        if question.ai_hint:
            content_parts.append(f"AI Hint: {question.ai_hint}")
        
        content_text = "\n".join(content_parts)
        
        metadata = {
            "entity_type": "activity_question",
            "entity_id": str(question.id),
            "activity_id": str(question.activity_id) if question.activity_id else None,
            "has_solution": bool(question.solution_steps),
            "has_answer": bool(question.answer),
            "has_hint": bool(question.ai_hint),
            "created_at": question.created_at.isoformat() if question.created_at else None,
            "content_length": len(content_text)
        }
        
        return content_text, metadata

class ActivityAIResponseExtractor(ContentExtractor):
    """Extract content from ActivityAIResponse model"""
    
    def extract_content(self, response: ActivityAIResponse) -> Tuple[str, Dict[str, Any]]:
        """Extract content from ActivityAIResponse"""
        content_text = response.ai_response or ""
        
        metadata = {
            "entity_type": "activity_ai_response",
            "entity_id": str(response.id),
            "session_id": str(response.session_id) if response.session_id else None,
            "user_id": str(response.user_id) if response.user_id else None,
            "question_id": str(response.question_id) if response.question_id else None,
            "created_at": response.created_at.isoformat() if response.created_at else None,
            "content_length": len(content_text)
        }
        
        return content_text, metadata

class ActivitySessionExtractor(ContentExtractor):
    """Extract content from ActivitySession model"""
    
    def extract_content(self, session: ActivitySession) -> Tuple[str, Dict[str, Any]]:
        """Extract content from ActivitySession"""
        content_parts = []
        
        # Session information
        content_parts.append(f"Activity Session")
        if session.status:
            content_parts.append(f"Status: {session.status.value}")
        if session.grade:
            content_parts.append(f"Grade: {session.grade}")
        if session.feedback:
            content_parts.append(f"Feedback: {session.feedback}")
        
        content_text = "\n".join(content_parts)
        
        metadata = {
            "entity_type": "activity_session",
            "entity_id": str(session.id),
            "activity_id": str(session.activity_id) if session.activity_id else None,
            "user_id": str(session.user_id) if session.user_id else None,
            "status": session.status.value if session.status else None,
            "grade": session.grade,
            "has_feedback": bool(session.feedback),
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "graded_at": session.graded_at.isoformat() if session.graded_at else None,
            "graded_by": str(session.graded_by) if session.graded_by else None,
            "content_length": len(content_text)
        }
        
        return content_text, metadata

class ActivityDocumentExtractor(ContentExtractor):
    """Extract content from ActivityDocument model"""
    
    def extract_content(self, document: ActivityDocument) -> Tuple[str, Dict[str, Any]]:
        """Extract content from ActivityDocument"""
        content_parts = []
        
        # Document information
        if document.file_name:
            content_parts.append(f"Document: {document.file_name}")
        if document.description:
            content_parts.append(f"Description: {document.description}")
        
        content_text = "\n".join(content_parts)
        
        metadata = {
            "entity_type": "activity_document",
            "entity_id": str(document.id),
            "activity_id": str(document.activity_id) if document.activity_id else None,
            "file_name": document.file_name,
            "file_type": document.file_type.value if document.file_type else None,
            "description": document.description,
            "file_metadata": document.file_metadata,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "content_length": len(content_text)
        }
        
        return content_text, metadata

class ActivityTemplateExtractor(ContentExtractor):
    """Extract content from ActivityTemplate model"""
    
    def extract_content(self, template: ActivityTemplate) -> Tuple[str, Dict[str, Any]]:
        """Extract content from ActivityTemplate"""
        content_parts = []
        
        # Template content
        if template.name:
            content_parts.append(f"Template: {template.name}")
        if template.description:
            content_parts.append(f"Description: {template.description}")
        if template.final_description:
            content_parts.append(f"Final Description: {template.final_description}")
        
        content_text = "\n".join(content_parts)
        
        metadata = {
            "entity_type": "activity_template",
            "entity_id": str(template.id),
            "name": template.name,
            "difficulty_level": template.difficulty_level.value if template.difficulty_level else None,
            "access_type": template.access_type.value if template.access_type else None,
            "category_id": str(template.category_id) if template.category_id else None,
            "sub_category_id": str(template.sub_category_id) if template.sub_category_id else None,
            "content_length": len(content_text)
        }
        
        return content_text, metadata

class UserExtractor(ContentExtractor):
    """Extract content from User model"""
    
    def extract_content(self, user: User) -> Tuple[str, Dict[str, Any]]:
        """Extract content from User"""
        content_parts = []
        
        # User information
        if user.name:
            content_parts.append(f"User: {user.name}")
        if user.email:
            content_parts.append(f"Email: {user.email}")
        if user.phone:
            content_parts.append(f"Phone: {user.phone}")
        if user.city:
            content_parts.append(f"City: {user.city}")
        if user.country:
            content_parts.append(f"Country: {user.country}")
        
        content_text = "\n".join(content_parts)
        
        metadata = {
            "entity_type": "user",
            "entity_id": str(user.id),
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "city": user.city,
            "country": user.country,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "content_length": len(content_text)
        }
        
        return content_text, metadata

# Registry of extractors
EXTRACTOR_REGISTRY = {
    "activity": ActivityExtractor(),
    "activity_question": ActivityQuestionExtractor(),
    "activity_ai_response": ActivityAIResponseExtractor(),
    "activity_session": ActivitySessionExtractor(),
    "activity_document": ActivityDocumentExtractor(),
    "activity_template": ActivityTemplateExtractor(),
    "user": UserExtractor(),
}

def get_extractor(entity_type: str) -> Optional[ContentExtractor]:
    """Get extractor for entity type"""
    return EXTRACTOR_REGISTRY.get(entity_type)

def extract_content_from_entity(entity: Any, entity_type: str) -> Tuple[str, Dict[str, Any]]:
    """Extract content from entity using appropriate extractor"""
    extractor = get_extractor(entity_type)
    if not extractor:
        logger.warning(f"No extractor found for entity type: {entity_type}")
        return "", {}
    
    try:
        return extractor.extract_content(entity)
    except Exception as e:
        logger.error(f"Error extracting content from {entity_type}: {e}")
        return "", {} 