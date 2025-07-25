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
    PermissionCreate,
    Permission as PermissionSchema,
)
from app.core.logger import get_logger
from uuid import UUID

# Initialize loggers
logger = get_logger(__name__)

router = APIRouter( tags=["roles"])

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
    Create a new role and optionally assign permissions.
    """
    logger.info(f"Creating new role: {role_in.name} by user: {current_user.email}")
    try:
        existing_role = db.query(Role).filter(Role.name == role_in.name).first()
        if existing_role:
            logger.warning(f"Role creation failed - name already exists: {role_in.name}")
            raise HTTPException(
                status_code=400,
                detail="Role with this name already exists",
            )
        
        # Create the Role
        role = Role(
            name=role_in.name,
            description=role_in.description,
            is_active=role_in.is_active,
        )
        db.add(role)
        db.commit()
        db.refresh(role)

        # Assign permissions if provided
        for permission_id in role_in.permissions:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            if not permission:
                logger.warning(f"Permission not found: {permission_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Permission with ID {permission_id} not found",
                )
            role_permission = RolePermission(
                role_id=role.id,
                permission_id=permission_id
            )
            db.add(role_permission)

        db.commit()

        # Reload role with permissions
        role = db.query(Role).filter(Role.id == role.id).first()
        logger.info(f"Successfully created role with permissions: {role.id}")
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

@router.post("/permissions/create", response_model=PermissionSchema)
def create_permission(
    *,
    db: Session = Depends(get_db),
    permission_in: PermissionCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new permission.
    """
    logger.info(f"Creating new permission: {permission_in.name} by user: {current_user.email}")
    try:
        existing_permission = db.query(Permission).filter(Permission.name == permission_in.name).first()
        if existing_permission:
            logger.warning(f"Permission creation failed - name already exists: {permission_in.name}")
            raise HTTPException(
                status_code=400,
                detail="Permission with this name already exists",
            )
        
        permission = Permission(
            name=permission_in.name,
            description=permission_in.description,
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        logger.info(f"Successfully created permission: {permission.id}")
        return permission

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating permission: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the permission"
        )

@router.get("/permissions", response_model=List[PermissionSchema])
def read_permissions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all permissions.
    """
    logger.info(f"Listing permissions for user: {current_user.email} (skip: {skip}, limit: {limit})")
    try:
        permissions = db.query(Permission).offset(skip).limit(limit).all()
        logger.info(f"Found {len(permissions)} permissions")
        return permissions
    except Exception as e:
        logger.error(f"Error listing permissions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching permissions"
        )

@router.get("/{role_id}/permissions/{permission_id}/check")
def check_role_permission(
    role_id: UUID,
    permission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Check if a role has a specific permission.
    """
    logger.info(f"Checking permission {permission_id} for role {role_id} by user: {current_user.email}")
    try:
        # Check if role exists
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            logger.warning(f"Role not found: {role_id}")
            raise HTTPException(
                status_code=404,
                detail="Role not found",
            )
        
        # Check if permission exists
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            logger.warning(f"Permission not found: {permission_id}")
            raise HTTPException(
                status_code=404,
                detail="Permission not found",
            )
        
        # Check if permission is assigned to role
        role_permission = db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
            RolePermission.is_active == True
        ).first()
        
        has_permission = role_permission is not None
        
        logger.info(f"Role {role_id} has permission {permission_id}: {has_permission}")
        return {
            "role_id": role_id,
            "permission_id": permission_id,
            "has_permission": has_permission,
            "role_name": role.name,
            "permission_name": permission.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking role permission: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while checking role permission"
        ) 