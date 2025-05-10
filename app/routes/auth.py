from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserCreate, User as UserSchema
from app.core.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signup", response_model=UserSchema)
def signup(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    logger.info(f"Attempting to create new user with email: {user_in.email}")
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        logger.warning(f"User creation failed - email already exists: {user_in.email}")
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    try:
        user = User(
            email=user_in.email,
            name=user_in.name,
            password=get_password_hash(user_in.password),
            phone=user_in.phone,
            city=user_in.city,
            country=user_in.country,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Successfully created new user: {user.email}")
        return user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the user."
        )

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logger.info(f"Successful login for user: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserSchema)
def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    logger.info(f"User profile accessed for: {current_user.email}")
    return current_user

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Logout current user.
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"} 