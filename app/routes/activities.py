from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse, PaginatedActivityResponse
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.activity_templates import ActivityTemplate
from app.core.logger import get_logger
from app.services.generate_clearification_questions import generate_clarification_questions
from app.services.generate_final_description import generate_final_description
from app.models.activity_sub_category import ActivitySubCategory
from app.models.activity_category import ActivityCategory
from app.schemas.activity import CategoryResponse, SubCategoryResponse, CategoryCreate,SubCategoryCreate,ClarificationQuestionsResponse,ClarificationAnswersRequest,FinalDescriptionResponse
from sqlalchemy.orm import joinedload
from app.models.document import Document as DocumentModel, DocumentChatSession, DocumentChatMessage
from app.schemas.document import (
    DocumentResponse, DocumentCreate, DocumentUpdate, DocumentUploadResponse,
    DocumentChatRequest, DocumentChatResponse, DocumentChatSessionResponse,
    DocumentChatMessageResponse
)
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.services.rag_chat_service import RAGChatService



# Initialize logger
logger = get_logger(__name__)

router = APIRouter(
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

@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new activity"""
    logger.info(f"Creating new activity: {activity.name} by user: {current_user.email}")
    try:
        db_activity = Activity(
            name=activity.name,
            description=activity.description,
            category_id=activity.category_id,
            sub_category_id=activity.sub_category_id,
            difficulty_level=activity.difficulty_level,
            access_type=activity.access_type,
            created_by=current_user.id,
            ai_guide=activity.ai_guide,
            final_description=activity.final_description
        )
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        logger.info(f"Successfully created activity: {db_activity.id}")
        return db_activity
    except Exception as e:
        logger.error(f"Error creating activity: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the activity"
        )

@router.get("/", response_model=PaginatedActivityResponse)
def list_activities(
    skip: int = 0,
    limit: int = 100,
    category_name: str = Query(None),
    subcategory_name: str = Query(None),
    activity_name: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all activities with pagination"""
    logger.info(f"Listing activities for user: {current_user.email} (skip: {skip}, limit: {limit})")
    logger.info(f"Filters - category_name: {category_name}, subcategory_name: {subcategory_name}, activity_name: {activity_name}")
    
    try:
        query = db.query(Activity)
        
        # Handle category and subcategory filters with proper JOINs
        if category_name or subcategory_name:
            # Always join both tables when either filter is present
            query = query.join(ActivityCategory).join(ActivitySubCategory)
            
            if category_name:
                query = query.filter(ActivityCategory.name.ilike(f"%{category_name}%"))
                logger.info(f"Applied category filter: {category_name}")
            
            if subcategory_name:
                query = query.filter(ActivitySubCategory.name.ilike(f"%{subcategory_name}%"))
                logger.info(f"Applied subcategory filter: {subcategory_name}")
        
        if activity_name:
            query = query.filter(Activity.name.ilike(f"%{activity_name}%"))
            logger.info(f"Applied activity name filter: {activity_name}")
        
        total_length = query.count()
        activities = query.offset(skip).limit(limit).all()
        logger.info(f"Found {len(activities)} activities out of {total_length} total")
        
        return PaginatedActivityResponse(
            items=activities,
            total_length=total_length,
            skip=skip,
            limit=limit,
            has_next=skip + limit < total_length,
            has_previous=skip > 0
        )
    except Exception as e:
        logger.error(f"Error listing activities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching activities"
        )

@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific activity details"""
    logger.info(f"Fetching activity {activity_id} for user: {current_user.email}")
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            logger.warning(f"Activity not found: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        logger.info(f"Successfully retrieved activity: {activity_id}")
        return activity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching activity {activity_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the activity"
        )

@router.put("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: UUID,
    activity_update: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update activity"""
    logger.info(f"Updating activity {activity_id} by user: {current_user.email}")
    try:
        db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not db_activity:
            logger.warning(f"Activity not found for update: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if db_activity.created_by != current_user.id:
            logger.warning(f"Unauthorized update attempt for activity {activity_id} by user: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this activity"
            )

        for field, value in activity_update.dict(exclude_unset=True).items():
            setattr(db_activity, field, value)

        db.commit()
        db.refresh(db_activity)
        logger.info(f"Successfully updated activity: {activity_id}")
        return db_activity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating activity {activity_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the activity"
        )

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete activity"""
    logger.info(f"Deleting activity {activity_id} by user: {current_user.email}")
    try:
        db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not db_activity:
            logger.warning(f"Activity not found for deletion: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if db_activity.created_by != current_user.id:
            logger.warning(f"Unauthorized deletion attempt for activity {activity_id} by user: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this activity"
            )

        # Check if activity has related data that might prevent deletion
        # This is optional but helps provide better error messages
        try:
            db.delete(db_activity)
            db.commit()
            logger.info(f"Successfully deleted activity: {activity_id}")
            return None
        except Exception as delete_error:
            db.rollback()
            logger.error(f"Database error during activity deletion {activity_id}: {str(delete_error)}")
            # Check if it's a foreign key constraint error
            if "foreign key constraint" in str(delete_error).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot delete activity because it has related data (sessions, questions, etc.). Please delete related data first."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while deleting the activity"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting activity {activity_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the activity"
        )

@router.post("/create_activity_with_template/{template_id}", response_model=ActivityResponse)
def create_activity_with_template(
    template_id: UUID,
    activity_data: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new activity using a template"""
    logger.info(f"Creating activity from template {template_id} by user: {current_user.email}")
    try:
        template = db.query(ActivityTemplate).filter(ActivityTemplate.id == template_id).first()
        if not template:
            logger.warning(f"Template not found: {template_id}")
            raise HTTPException(status_code=404, detail="Template not found")

        db_activity = Activity(
            name=template.name,
            description=template.description,
            category_id=template.category_id,
            sub_category_id=template.sub_category_id,
            difficulty_level=template.difficulty_level,
            access_type=template.access_type,
            created_by=current_user.id,
            ai_guide=activity_data.ai_guide,
            final_description=activity_data.final_description
        )

        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        logger.info(f"Successfully created activity from template: {db_activity.id}")
        return db_activity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating activity from template {template_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the activity from template"
        )

@router.post("/{activity_id}/generate-clarification-questions", response_model=ClarificationQuestionsResponse)
async def generate_activity_clarification_questions(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate 5 clarification questions for an activity using AI"""
    logger.info(f"Generating clarification questions for activity {activity_id} by user: {current_user.email}")
    
    # Get the activity first, outside the try block
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        logger.warning(f"Activity not found: {activity_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    try:
        # Prepare activity details for the template
        activity_details = {
            "name": activity.name,
            "description": activity.description,
            "level": activity.difficulty_level.value if activity.difficulty_level else None,  # Convert enum to string
            "category_name": activity.category.name if activity.category else None,
            "sub_category_name": activity.sub_category.name if activity.sub_category else None
        }

        # Generate exactly 5 clarification questions using the template
        questions = await generate_clarification_questions(activity_details)
        
        # Format questions with unique IDs
        formatted_questions = [
            {
                "id": f"q_{i+1}",
                "text": question
            }
            for i, question in enumerate(questions[:5])  # Ensure exactly 5 questions
        ]
        
        # Store the questions in the activity
        activity.clarification_questions = formatted_questions
        db.commit()
        
        logger.info(f"Successfully generated and stored 5 clarification questions for activity: {activity_id}")
        return ClarificationQuestionsResponse(
            activity_id=activity_id,
            questions=formatted_questions,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error generating clarification questions for activity {activity_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating clarification questions: {str(e)}"
        )

@router.post("/{activity_id}/generate-final-description", response_model=FinalDescriptionResponse)
async def generate_activity_final_description(
    activity_id: UUID,
    answers_request: ClarificationAnswersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate final description for an activity using AI based on clarification answers"""
    logger.info(f"Generating final description for activity {activity_id} by user: {current_user.email}")
    try:
        # Get the activity
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            logger.warning(f"Activity not found: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )

        # Verify that clarification questions exist
        if not activity.clarification_questions:
            logger.warning(f"No clarification questions found for activity: {activity_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clarification questions must be generated first"
            )

        # Get all question IDs and provided answer IDs
        question_ids = {q["id"] for q in activity.clarification_questions}
        answer_ids = set(answers_request.answers.keys())
        
        # Check for extra answers (answers for non-existent questions)
        extra_answers = answer_ids - question_ids
        if extra_answers:
            logger.warning(f"Extra answers provided for non-existent questions: {extra_answers}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extra answers provided for non-existent questions: {', '.join(extra_answers)}"
            )

        # Filter out empty answers and prepare Q&A pairs
        qa_pairs = []
        for q_id, answer in answers_request.answers.items():
            if answer and answer.strip():  # Only include non-empty answers
                question_text = next(q["text"] for q in activity.clarification_questions if q["id"] == q_id)
                qa_pairs.append({
                    "question": question_text,
                    "answer": answer.strip()
                })

        # Log which questions were answered and which were skipped
        answered_questions = set(answers_request.answers.keys())
        skipped_questions = question_ids - answered_questions
        if skipped_questions:
            skipped_questions_text = [
                next(q["text"] for q in activity.clarification_questions if q["id"] == q_id)
                for q_id in skipped_questions
            ]
            logger.info(f"Questions skipped (no answers provided): {skipped_questions_text}")

        # Prepare activity details for the template
        activity_details = {
            "name": activity.name,
            "description": activity.description,
            "level": activity.difficulty_level.value if activity.difficulty_level else None,  # Convert enum to string
            "category_name": activity.category.name if activity.category else None,
            "sub_category_name": activity.sub_category.name if activity.sub_category else None
        }

        # Generate final description using the template with available Q&A pairs
        final_description = await generate_final_description(
            activity_details=activity_details,
            clarification_qa=qa_pairs
        )
        
        # Update activity with the final description
        activity.final_description = final_description
        db.commit()
        
        logger.info(f"Successfully generated final description for activity: {activity_id} with {len(qa_pairs)} answered questions")
        return FinalDescriptionResponse(
            activity_id=activity_id,
            final_description=final_description,
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating final description for activity {activity_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating final description: {str(e)}"
        ) 
    

@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch a single activity by its ID, including category and sub-category"
)
def get_activity_by_id(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} fetching activity {activity_id}")
    activity = (
        db.query(Activity)
          .options(
              joinedload(Activity.category),
              joinedload(Activity.sub_category)
          )
          .filter(Activity.id == activity_id)
          .first()
    )
    if not activity:
        logger.warning(f"Activity not found: {activity_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    return activity

async def extract_list_filters(prompt: str) -> dict:
    extraction_prompt = f"""
    Extract activity listing filters from this user request. Return JSON with these fields:
    - activity_name: The activity name/title to filter (or null)
    - category_name: The subject/category to filter (or null)
    - subcategory_name: The specific topic/subcategory to filter (or null)

    User request: "{prompt}"

    Examples:
    - "Show me all activities" → {{"activity_name": null, "category_name": null, "subcategory_name": null}}
    - "List math quizzes for trignometry" → {{"activity_name": "quiz", "category_name": "math", "subcategory_name": trignometry}}
    - "Get activities for algebra" → {{"activity_name": null, "category_name": null, "subcategory_name": "algebra"}}
    - "Show all physics activities" → {{"activity_name": null, "category_name": "physics", "subcategory_name": null}}
    """
    result = await chat_completion({"prompt": extraction_prompt}, {}, json_mode=True)
    return result.get("response", {})

async def route_activity(state: dict, config: dict) -> dict:
    logger.debug(f"=== ROUTE_ACTIVITY START ===")
    op = state.get("operation")
    logger.debug(f"route_activity op: {op}")

    if op == "list-activities":
        prompt = state.get("prompt", "")
        filters = await extract_list_filters(prompt)
        logger.debug(f"Extracted filters for list-activities: activity_name={filters.get('activity_name')}, category_name={filters.get('category_name')}, subcategory_name={filters.get('subcategory_name')}")
        payload = {**state.get("details", {}), **filters}
        result = await activity_crud({"operation": op, "payload": payload}, {})
        return result.get("result", {})
    elif op == "unknown":
        result = {"error": "Could not determine intent, please rephrase."}
        logger.debug(f"Unknown operation, returning error: {result}")
        return result

    result = await activity_crud({"operation": op, "payload": state.get("details", {})}, {})
    return result.get("result", {})

# ================================
# Document APIs (RAG System)
# ================================

# Initialize document services
document_processor = DocumentProcessor()
vector_store_service = VectorStoreService()
rag_chat_service = RAGChatService()

@router.post("/{activity_id}/documents/upload", response_model=DocumentUploadResponse)
async def upload_document_to_activity(
    activity_id: UUID,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string of tags
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process a document for an activity"""
    
    try:
        # Validate file type
        allowed_types = ["application/pdf", "text/plain", "text/csv", "application/json"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not supported. Allowed types: {allowed_types}"
            )
        
        # Verify activity exists and user has access
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check if user has permission to upload to this activity
        if activity.created_by != current_user.id and activity.access_type.value != "global":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to upload documents to this activity"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Process tags
        tag_list = []
        if tags:
            try:
                import json
                tag_list = json.loads(tags)
            except json.JSONDecodeError:
                logger.warning(f"Invalid tags JSON: {tags}")
        
        # Process document
        document = await document_processor.process_uploaded_file(
            file_content=file_content,
            filename=file.filename,
            mime_type=file.content_type,
            activity_id=str(activity_id),
            uploaded_by=str(current_user.id),
            db=db
        )
        
        # Update document with additional info
        if description:
            document.description = description
        if tag_list:
            document.tags = tag_list
        
        # Get document chunks
        chunks = document_processor.get_document_chunks(document)
        
        # Add to vector store
        if chunks:
            success = await vector_store_service.add_document_to_vector_store(document, chunks)
            if not success:
                logger.warning(f"Failed to add document {document.id} to vector store")
        
        db.commit()
        
        return DocumentUploadResponse(
            document_id=document.id,
            activity_id=activity_id,
            message="Document uploaded and processed successfully",
            processing_status="completed" if document.is_processed else "failed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("/{activity_id}/documents", response_model=List[DocumentResponse])
async def list_activity_documents(
    activity_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents for a specific activity"""
    
    try:
        # Verify activity exists
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check access permissions
        if activity.created_by != current_user.id and activity.access_type.value != "global":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this activity"
            )
        
        documents = db.query(DocumentModel).filter(
            DocumentModel.activity_id == activity_id
        ).offset(skip).limit(limit).all()
        
        return documents
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing activity documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing activity documents"
        )

@router.get("/{activity_id}/documents/{document_id}", response_model=DocumentResponse)
async def get_activity_document(
    activity_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document from an activity"""
    
    try:
        # Verify activity exists
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check access permissions
        if activity.created_by != current_user.id and activity.access_type.value != "global":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this activity"
            )
        
        # Get document
        document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id,
            DocumentModel.activity_id == activity_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting document"
        )

@router.delete("/{activity_id}/documents/{document_id}")
async def delete_activity_document(
    activity_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document from an activity"""
    
    try:
        # Verify activity exists
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Get document
        document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id,
            DocumentModel.activity_id == activity_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user can delete (only uploader or activity creator)
        if (document.uploaded_by != current_user.id and 
            activity.created_by != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this document"
            )
        
        # Delete from vector store
        await vector_store_service.delete_document_from_vector_store(str(document.id))
        
        # Delete document
        await document_processor.delete_document(document, db)
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting document"
        )

@router.post("/{activity_id}/documents/chat", response_model=DocumentChatResponse)
async def chat_with_activity_documents(
    activity_id: UUID,
    request: DocumentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Chat with all documents in an activity using RAG"""
    
    try:
        # Verify activity exists and user has access
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if activity.created_by != current_user.id and activity.access_type.value != "global":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this activity"
            )
        
        # Chat with activity documents
        response = await rag_chat_service.chat_with_activity_documents(
            message=request.message,
            activity_id=activity_id,
            user_id=current_user.id,
            session_name=None,
            db=db
        )
        
        return DocumentChatResponse(
            message=response["message"],
            session_id=response["session_id"],
            sources=response["sources"],
            metadata=response["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in activity document chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in activity document chat"
        )

@router.post("/{activity_id}/documents/{document_id}/chat", response_model=DocumentChatResponse)
async def chat_with_specific_document(
    activity_id: UUID,
    document_id: UUID,
    request: DocumentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Chat with a specific document in an activity using RAG"""
    
    try:
        # Verify activity exists and user has access
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if activity.created_by != current_user.id and activity.access_type.value != "global":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this activity"
            )
        
        # Verify document exists and belongs to activity
        document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id,
            DocumentModel.activity_id == activity_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get or create session
        session = await rag_chat_service.get_or_create_session(
            session_id=request.session_id,
            document_id=document_id,
            activity_id=activity_id,
            user_id=current_user.id,
            session_name=None,
            db=db
        )
        
        # Chat with document
        response = await rag_chat_service.chat_with_document(
            message=request.message,
            session_id=session.id,
            db=db
        )
        
        return DocumentChatResponse(
            message=response["message"],
            session_id=response["session_id"],
            sources=response["sources"],
            metadata=response["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in document chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in document chat"
        )

@router.get("/{activity_id}/documents/chat/sessions", response_model=List[DocumentChatSessionResponse])
async def list_activity_chat_sessions(
    activity_id: UUID,
    document_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List chat sessions for an activity"""
    
    try:
        # Verify activity exists and user has access
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if activity.created_by != current_user.id and activity.access_type.value != "global":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this activity"
            )
        
        query = db.query(DocumentChatSession).filter(
            DocumentChatSession.user_id == current_user.id,
            DocumentChatSession.activity_id == activity_id
        )
        
        if document_id:
            query = query.filter(DocumentChatSession.document_id == document_id)
        
        sessions = query.order_by(DocumentChatSession.updated_at.desc()).all()
        return sessions
        
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing chat sessions"
        )

@router.get("/{activity_id}/documents/stats")
async def get_activity_document_stats(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document statistics for a specific activity"""
    
    try:
        # Verify activity exists and user has access
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if activity.created_by != current_user.id and activity.access_type.value != "global":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this activity"
            )
        
        # Get activity's document count
        document_count = db.query(DocumentModel).filter(
            DocumentModel.activity_id == activity_id
        ).count()
        
        # Get processed document count
        processed_count = db.query(DocumentModel).filter(
            DocumentModel.activity_id == activity_id,
            DocumentModel.is_processed == True
        ).count()
        
        # Get vector store stats for this activity
        activity_chunks = await vector_store_service.get_activity_chunks_from_vector_store(str(activity_id))
        
        return {
            "activity_id": activity_id,
            "total_documents": document_count,
            "processed_documents": processed_count,
            "total_chunks": len(activity_chunks),
            "activity_name": activity.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity document stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting activity document stats"
        )