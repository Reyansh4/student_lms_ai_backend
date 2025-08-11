# Import all models here to ensure they are registered with SQLAlchemy
# This file should be imported after all models are defined

from app.models.user import User
from app.models.activity import Activity
from app.models.activity_session import ActivitySession
from app.models.conversation import Conversation
from app.models.activity_chat import ActivityChat
from app.models.chat_message import ChatMessage

# Add any other models here as they are created 