from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.schemas.profile import ProfileUpdate, PasswordChange
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.core.security import verify_password

router = APIRouter()


@router.get("/profile", response_model=UserResponse, summary="Get Profile")
def read_profile(current_user: User = Depends(get_current_active_user)):
    """Retrieve current user's profile information."""
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse, summary="Update Profile")
def update_profile(
    request: Request,
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update profile information (name, email). Does NOT allow changing role or status."""
    client_ip = request.client.host if request.client else "unknown"
    
    if profile_in.email and profile_in.email.lower() != current_user.email.lower():
        existing_user = UserService.get_by_email(db, profile_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered to another user"
            )
            
    updated_user = UserService.update(
        db,
        db_user=current_user,
        user_in=profile_in # type: ignore
    )
    
    AuditService.create_log(
        db=db,
        action="PROFILE_UPDATE",
        actor_id=current_user.id,
        actor_email=current_user.email,
        ip_address=client_ip,
        metadata={"updated_fields": list(profile_in.model_dump(exclude_unset=True).keys())}
    )
    
    return UserResponse.model_validate(updated_user)


@router.post("/profile/change-password", summary="Change Password")
def change_password(
    request: Request,
    pw_in: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Securely change current user's password."""
    client_ip = request.client.host if request.client else "unknown"
    
    if not verify_password(pw_in.current_password, current_user.password_hash):
        AuditService.create_log(
            db=db,
            action="PASSWORD_CHANGE_FAILED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            ip_address=client_ip,
            metadata={"reason": "Incorrect current password"}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
        
    UserService.change_password(db, db_user=current_user, new_password=pw_in.new_password)
    
    AuditService.create_log(
        db=db,
        action="PASSWORD_CHANGE_SUCCESS",
        actor_id=current_user.id,
        actor_email=current_user.email,
        ip_address=client_ip
    )
    
    return {"message": "Password changed successfully."}
