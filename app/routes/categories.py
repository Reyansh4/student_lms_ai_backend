from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.activity_templates import ActivityTemplate
from app.core.logger import get_logger
from app.models.activity_sub_category import ActivitySubCategory
from app.models.activity_category import ActivityCategory


# Category Schemas
class CategoryCreate(BaseModel):
    name: str
    description: str = ""

class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str

    class Config:
        orm_mode = True

# SubCategory Schemas
class SubCategoryCreate(BaseModel):
    category_id: UUID
    name: str
    description: str = ""

class SubCategoryResponse(BaseModel):
    id: UUID
    category_id: UUID
    name: str
    description: str

    class Config:
        orm_mode = True


# Initialize logger
logger = get_logger(__name__)

router = APIRouter(
    prefix="/activities",
    tags=["activities"]
)

# ================================
# Category APIs
# ================================

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new activity category"""
    logger.info(f"User {current_user.email} is creating category: {category.name}")
    try:
        db_category = ActivityCategory(
            name=category.name,
            description=category.description
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        logger.info(f"Category created successfully: {db_category.id}")
        return db_category
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the category"
        )

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all activity categories"""
    logger.info(f"User {current_user.email} is requesting category list")
    try:
        categories = db.query(ActivityCategory).all()
        logger.info(f"Found {len(categories)} categories")
        return categories
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching categories"
        )


# ================================
# SubCategory APIs
# ================================

@router.post("/subcategories", response_model=SubCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_subcategory(
    subcategory: SubCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new subcategory under a specific category"""
    logger.info(f"User {current_user.email} is creating subcategory: {subcategory.name} in category {subcategory.category_id}")
    try:
        # Optional: validate if the category exists
        category = db.query(ActivityCategory).filter(ActivityCategory.id == subcategory.category_id).first()
        if not category:
            logger.warning(f"Category not found: {subcategory.category_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )

        db_subcategory = ActivitySubCategory(
            category_id=subcategory.category_id,
            name=subcategory.name,
            description=subcategory.description
        )
        db.add(db_subcategory)
        db.commit()
        db.refresh(db_subcategory)
        logger.info(f"Successfully created subcategory: {db_subcategory.id}")
        return db_subcategory
    except Exception as e:
        logger.error(f"Error creating subcategory: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the subcategory"
        )



@router.get("/categories/{category_id}/subcategories", response_model=List[SubCategoryResponse])
def list_subcategories_by_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all subcategories for a given category"""
    logger.info(f"User {current_user.email} is requesting subcategories for category: {category_id}")
    try:
        subcategories = db.query(ActivitySubCategory).filter(
            ActivitySubCategory.category_id == category_id
        ).all()

        logger.info(f"Found {len(subcategories)} subcategories for category {category_id}")
        return subcategories
    except Exception as e:
        logger.error(f"Error fetching subcategories for category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching subcategories"
        )


# AI Agent :-
# Input :- User Input, activity_final description, document(optional)

# It will call prompt template in which you have input. It will be zero shots. 