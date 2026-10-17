from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserRoleUpdate, UserStatusUpdate
from app.services.user_service import UserService
from app.services.audit_service import AuditService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/users", response_model=List[UserResponse], summary="List All Users (Admin Only)")
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retrieve list of system users."""
    users = UserService.get_multi(db, skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create User (Admin Only)")
def create_user(
    request: Request,
    user_in: UserCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user with assigned role (ADMIN or OPERATOR)."""
    client_ip = request.client.host if request.client else "unknown"
    existing_user = UserService.get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )

    new_user = UserService.create(db, user_in=user_in)
    
    AuditService.create_log(
        db=db,
        action="USER_CREATED",
        actor_id=current_admin.id,
        actor_email=current_admin.email,
        ip_address=client_ip,
        metadata={"created_user_id": new_user.id, "created_email": new_user.email, "role": new_user.role.value}
    )

    return UserResponse.model_validate(new_user)


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get User Details (Admin Only)")
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve specific user details by ID."""
    user = UserService.get_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse, summary="Update User Details (Admin Only)")
def update_user(
    request: Request,
    user_id: int,
    user_in: UserUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user details."""
    client_ip = request.client.host if request.client else "unknown"
    db_user = UserService.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_user = UserService.update(db, db_user=db_user, user_in=user_in)

    AuditService.create_log(
        db=db,
        action="USER_UPDATED_BY_ADMIN",
        actor_id=current_admin.id,
        actor_email=current_admin.email,
        ip_address=client_ip,
        metadata={"target_user_id": user_id, "updated_fields": list(user_in.model_dump(exclude_unset=True).keys())}
    )

    return UserResponse.model_validate(updated_user)


@router.patch("/users/{user_id}/role", response_model=UserResponse, summary="Update User Role (Admin Only)")
def update_user_role(
    request: Request,
    user_id: int,
    role_in: UserRoleUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update assigned role of a user."""
    client_ip = request.client.host if request.client else "unknown"
    db_user = UserService.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if db_user.id == current_admin.id and role_in.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-demotion: You cannot remove ADMIN role from your own active account."
        )

    updated_user = UserService.update_role(db, db_user=db_user, role=role_in.role)

    AuditService.create_log(
        db=db,
        action="ROLE_CHANGE",
        actor_id=current_admin.id,
        actor_email=current_admin.email,
        ip_address=client_ip,
        metadata={"target_user_id": user_id, "target_email": db_user.email, "new_role": role_in.role.value}
    )

    return UserResponse.model_validate(updated_user)


@router.patch("/users/{user_id}/status", response_model=UserResponse, summary="Toggle User Active Status (Admin Only)")
def update_user_status(
    request: Request,
    user_id: int,
    status_in: UserStatusUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a user account."""
    client_ip = request.client.host if request.client else "unknown"
    db_user = UserService.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if db_user.id == current_admin.id and not status_in.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-deactivation: You cannot deactivate your own active account."
        )

    updated_user = UserService.update_status(db, db_user=db_user, is_active=status_in.is_active)

    AuditService.create_log(
        db=db,
        action="USER_STATUS_CHANGE",
        actor_id=current_admin.id,
        actor_email=current_admin.email,
        ip_address=client_ip,
        metadata={"target_user_id": user_id, "is_active": status_in.is_active}
    )

    return UserResponse.model_validate(updated_user)
