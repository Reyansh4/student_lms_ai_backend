# Import the Base class
from app.db.base_class import Base

# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.models.activity import Activity
from app.models.activity_category import ActivityCategory
from app.models.activity_sub_category import ActivitySubCategory
from app.models.activity_question import ActivityQuestion
from app.models.activity_session import ActivitySession
from app.models.activity_document import ActivityDocument
from app.models.activity_ai_response import ActivityAIResponse
from app.models.document import Document, DocumentChatSession, DocumentChatMessage
from app.models.evaluation import EvaluationResult, QuizQuestion, LearningProgress 