from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.schemas.role import (
    RoleCreate,
    Role as RoleSchema,
    RolePermissionCreate,
)
from app.core.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("/", response_model=List[RoleSchema])
def read_roles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all roles.
    """
    logger.info(f"Listing roles for user: {current_user.email} (skip: {skip}, limit: {limit})")
    try:
        roles = db.query(Role).offset(skip).limit(limit).all()
        logger.info(f"Found {len(roles)} roles")
        return roles
    except Exception as e:
        logger.error(f"Error listing roles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching roles"
        )

@router.post("/", response_model=RoleSchema)
def create_role(
    *,
    db: Session = Depends(get_db),
    role_in: RoleCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new role.
    """
    logger.info(f"Creating new role: {role_in.name} by user: {current_user.email}")
    try:
        # Check if role with same name exists
        existing_role = db.query(Role).filter(Role.name == role_in.name).first()
        if existing_role:
            logger.warning(f"Role creation failed - name already exists: {role_in.name}")
            raise HTTPException(
                status_code=400,
                detail="Role with this name already exists",
            )
        
        role = Role(
            name=role_in.name,
            description=role_in.description,
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        logger.info(f"Successfully created role: {role.id}")
        return role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating role: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the role"
        )

@router.post("/permissions", response_model=RoleSchema)
def assign_permission_to_role(
    *,
    db: Session = Depends(get_db),
    permission_in: RolePermissionCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Assign permission to role.
    """
    logger.info(f"Assigning permission {permission_in.permission_id} to role {permission_in.role_id} by user: {current_user.email}")
    try:
        role = db.query(Role).filter(Role.id == permission_in.role_id).first()
        if not role:
            logger.warning(f"Role not found: {permission_in.role_id}")
            raise HTTPException(
                status_code=404,
                detail="Role not found",
            )
        
        permission = db.query(Permission).filter(Permission.id == permission_in.permission_id).first()
        if not permission:
            logger.warning(f"Permission not found: {permission_in.permission_id}")
            raise HTTPException(
                status_code=404,
                detail="Permission not found",
            )
        
        # Check if permission is already assigned to role
        existing_permission = db.query(RolePermission).filter(
            RolePermission.role_id == permission_in.role_id,
            RolePermission.permission_id == permission_in.permission_id
        ).first()
        
        if existing_permission:
            logger.warning(f"Permission {permission_in.permission_id} already assigned to role {permission_in.role_id}")
            raise HTTPException(
                status_code=400,
                detail="Permission already assigned to role",
            )
        
        role_permission = RolePermission(
            role_id=permission_in.role_id,
            permission_id=permission_in.permission_id,
        )
        db.add(role_permission)
        db.commit()
        db.refresh(role)
        logger.info(f"Successfully assigned permission {permission_in.permission_id} to role {permission_in.role_id}")
        return role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning permission to role: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while assigning permission to role"
        ) 