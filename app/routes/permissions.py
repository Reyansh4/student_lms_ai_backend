from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from uuid import UUID
from app.api.deps import get_db, get_current_active_user
from app.models.permission import Permission as PermissionModel
from app.schemas.permission import Permission, PermissionCreate, PermissionUpdate
from app.core.logger import get_logger

router = APIRouter(

    tags=["permissions"]
)
logger = get_logger(__name__)

@router.get("/", response_model=List[Permission])
def read_permissions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    logger.info(f"Listing permissions for user: {current_user.email} (skip={skip}, limit={limit})")
    permissions = db.query(PermissionModel).offset(skip).limit(limit).all()
    return permissions

@router.get("/{permission_id}", response_model=Permission)
def read_permission(
    permission_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    logger.info(f"Fetching permission {permission_id} by user: {current_user.email}")
    permission = db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()
    if not permission:
        logger.warning(f"Permission not found: {permission_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return permission

@router.post("/", response_model=Permission, status_code=status.HTTP_201_CREATED)
def create_permission(
    *,
    db: Session = Depends(get_db),
    permission_in: PermissionCreate,
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    logger.info(f"Creating permission {permission_in.name} by user: {current_user.email}")
    existing = db.query(PermissionModel).filter(PermissionModel.name == permission_in.name).first()
    if existing:
        logger.warning(f"Permission creation failed - name exists: {permission_in.name}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission name already exists")
    permission = PermissionModel(**permission_in.dict())
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission

@router.put("/{permission_id}", response_model=Permission)
def update_permission(
    permission_id: UUID,
    *,
    db: Session = Depends(get_db),
    permission_in: PermissionUpdate,
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    logger.info(f"Updating permission {permission_id} by user: {current_user.email}")
    permission = db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()
    if not permission:
        logger.warning(f"Permission not found: {permission_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    for field, value in permission_in.dict(exclude_unset=True).items():
        setattr(permission, field, value)
    db.commit()
    db.refresh(permission)
    return permission

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_permission(
    permission_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
) -> None:
    logger.info(f"Deleting permission {permission_id} by user: {current_user.email}")
    permission = db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()
    if not permission:
        logger.warning(f"Permission not found: {permission_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    db.delete(permission)
    db.commit()
    return
