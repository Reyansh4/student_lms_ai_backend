from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey, Float, Integer, Boolean, JSON, func, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid
import enum

class EvaluationType(enum.Enum):
    QUIZ = "quiz"
    PROGRESS = "progress"
    DOCUMENT = "document"
    COMPREHENSIVE = "comprehensive"

class EvaluationStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=False)
    session_id = Column(UUID, ForeignKey("activity_sessions.id"), nullable=True)
    
    # Evaluation metadata
    evaluation_type = Column(Enum(EvaluationType), nullable=False)
    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.PENDING)
    triggered_by = Column(String(50), nullable=False)  # "chat" or "ui"
    
    # Scores and metrics
    overall_score = Column(Float, nullable=True)
    accuracy_percentage = Column(Float, nullable=True)
    difficulty_breakdown = Column(JSON, nullable=True)  # {"easy": 85, "medium": 70, "hard": 60}
    
    # Analysis results
    strengths = Column(JSON, nullable=True)  # List of strengths
    weaknesses = Column(JSON, nullable=True)  # List of weaknesses
    improvements = Column(JSON, nullable=True)  # List of suggested improvements
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    
    # Context and data
    chat_context = Column(JSON, nullable=True)  # Relevant chat history
    document_context = Column(JSON, nullable=True)  # Relevant document references
    quiz_responses = Column(JSON, nullable=True)  # Quiz answers and correct answers
    
    # Generated content
    follow_up_questions = Column(JSON, nullable=True)  # Generated questions
    knowledge_gaps = Column(JSON, nullable=True)  # Identified knowledge gaps
    learning_path = Column(JSON, nullable=True)  # Suggested learning path
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="evaluations")
    activity = relationship("Activity", back_populates="evaluations")
    session = relationship("ActivitySession", back_populates="evaluations")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(UUID, ForeignKey("evaluation_results.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=True)
    difficulty_level = Column(String(20), nullable=True)  # easy, medium, hard
    explanation = Column(Text, nullable=True)
    points = Column(Float, default=1.0)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    evaluation = relationship("EvaluationResult", back_populates="quiz_questions")

class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    activity_id = Column(UUID, ForeignKey("activity.id"), nullable=False)
    
    # Progress metrics
    time_spent = Column(Integer, nullable=True)  # in seconds
    completion_percentage = Column(Float, default=0.0)
    engagement_score = Column(Float, nullable=True)
    difficulty_progression = Column(JSON, nullable=True)  # Track difficulty changes
    
    # Learning patterns
    study_patterns = Column(JSON, nullable=True)  # Time of day, duration, etc.
    concept_mastery = Column(JSON, nullable=True)  # Mastery level per concept
    learning_style = Column(String(50), nullable=True)  # visual, auditory, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="learning_progress")
    activity = relationship("Activity", back_populates="learning_progress") 