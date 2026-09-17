from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and issue JWT access token",
    description="Authenticates operator or administrator credentials and returns a signed JWT bearer token.",
    responses={
        401: {"description": "Invalid username or password"}
    }
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.execute(
        select(User).where(User.username == login_data.username.strip())
    ).scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.username,
        role=user.role,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
    )
