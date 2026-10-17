from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/auth/login", response_model=Token, summary="User Authentication Login")
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user with email and password, return JWT token."""
    client_ip = request.client.host if request.client else "unknown"
    user = UserService.authenticate(db, email=form_data.username, password=form_data.password)
    
    if not user:
        AuditService.create_log(
            db=db,
            action="LOGIN_FAILED",
            actor_email=form_data.username,
            ip_address=client_ip,
            metadata={"reason": "Invalid email or password"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        AuditService.create_log(
            db=db,
            action="LOGIN_BLOCKED_INACTIVE",
            actor_id=user.id,
            actor_email=user.email,
            ip_address=client_ip,
            metadata={"reason": "User account is deactivated"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Contact System Administrator."
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value
    )
    
    AuditService.create_log(
        db=db,
        action="LOGIN_SUCCESS",
        actor_id=user.id,
        actor_email=user.email,
        ip_address=client_ip,
        metadata={"role": user.role.value}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/auth/me", response_model=UserResponse, summary="Get Current Authenticated User")
def get_me(current_user: User = Depends(get_current_active_user)):
    """Return the profile details of the currently authenticated active user."""
    return UserResponse.model_validate(current_user)


@router.post("/auth/logout", summary="Logout User Session")
def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Record logout audit event. JWT tokens are stateless; client discards token."""
    client_ip = request.client.host if request.client else "unknown"
    AuditService.create_log(
        db=db,
        action="LOGOUT",
        actor_id=current_user.id,
        actor_email=current_user.email,
        ip_address=client_ip
    )
    return {"message": "Successfully logged out session."}
