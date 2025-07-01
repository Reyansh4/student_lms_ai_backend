# app/agent/tools/activity_tools.py
from typing_extensions import TypedDict
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.db.session import get_db
from sqlalchemy.exc import NoResultFound
from uuid import UUID

from app.models.activity_category import ActivityCategory
from app.models.activity_sub_category import ActivitySubCategory
from app.models.activity import Activity, DifficultyLevel, AccessType

logger = get_logger(__name__)

class CreateActivityInput(TypedDict):
    name: str
    description: str
    category_id: str  # UUID of the category
    sub_category_id: str  # UUID of the subcategory
    difficulty_level: str  # "Beginner"|"Intermediate"|"Advanced"

class CreateActivityOutput(TypedDict):
    id: str
    name: str
    description: str
    category: str
    subcategory: str
    difficulty_level: str
    access_type: str
    created_at: str

@tool(return_direct=True)
def create_activity(payload: CreateActivityInput) -> CreateActivityOutput:
    """
    Create a new Activity (always PRIVATE) in the DB.
    Expects a dict with keys: name, description, category_id,
    sub_category_id, difficulty_level.
    Returns the created record.
    """
    db = next(get_db())
    try:
        logger.info(f"Creating activity with payload: {payload}")
        
        # 1) Get category by ID
        category_id = payload["category_id"]
        logger.info(f"Looking for category with ID: {category_id}")
        # Convert string to UUID if needed
        if isinstance(category_id, str):
            category_id = UUID(category_id)
        category = db.query(ActivityCategory).filter(ActivityCategory.id == category_id).first()
        if not category:
            raise ValueError(f"Category with ID {category_id} not found")
        logger.info(f"Found category: {category.name}")

        # 2) Get subcategory by ID
        subcategory_id = payload["sub_category_id"]
        logger.info(f"Looking for subcategory with ID: {subcategory_id}")
        # Convert string to UUID if needed
        if isinstance(subcategory_id, str):
            subcategory_id = UUID(subcategory_id)
        subcat = db.query(ActivitySubCategory).filter(ActivitySubCategory.id == subcategory_id).first()
        if not subcat:
            raise ValueError(f"Subcategory with ID {subcategory_id} not found")
        logger.info(f"Found subcategory: {subcat.name}")

        # 3) Create activity
        activity = Activity(
            name=payload["name"],
            description=payload.get("description", ""),
            category_id=category.id,
            sub_category_id=subcat.id,
            difficulty_level=DifficultyLevel(payload["difficulty_level"]),
            access_type=AccessType.PRIVATE,  # Always PRIVATE
            created_by=payload.get("created_by")  # assuming you pass user_id here
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        
        logger.info(f"Successfully created activity: {activity.name} with ID: {activity.id}")

        return CreateActivityOutput({
            "id": str(activity.id),
            "name": activity.name,
            "description": activity.description,
            "category": category.name,
            "subcategory": subcat.name,
            "difficulty_level": activity.difficulty_level.value,
            "access_type": activity.access_type.value,
            "created_at": activity.created_at.isoformat(),
        })

    except Exception as e:
        db.rollback()
        logger.error(f"create_activity failed: {e}")
        raise
