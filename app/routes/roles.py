from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.deps import get_db, get_current_active_user
from models.user import User
from models.role import Role
from models.permission import Permission
from models.role_permission import RolePermission
from schemas.role import (
    RoleCreate,
    Role as RoleSchema,
    RolePermissionCreate,
)

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
    roles = db.query(Role).offset(skip).limit(limit).all()
    return roles

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
    # Check if role with same name exists
    existing_role = db.query(Role).filter(Role.name == role_in.name).first()
    if existing_role:
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
    return role

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
    role = db.query(Role).filter(Role.id == permission_in.role_id).first()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_in.permission_id).first()
    if not permission:
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
    return role 