from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token, oauth2_scheme
)
from app.models.models import User, UserRole
from app.schemas.auth_schema import UserCreate, UserResponse, Token, UserLogin

router = APIRouter()

# Default admin/operator credentials for quick testing
DEMO_USERS = {
    "operator@metroflow.com": {
        "id": 1,
        "email": "operator@metroflow.com",
        "full_name": "Metro Control Operator",
        "hashed_password": get_password_hash("operator123"),
        "role": UserRole.OPERATOR,
        "assigned_station_id": 1,
        "is_active": True,
    },
    "admin@metroflow.com": {
        "id": 2,
        "email": "admin@metroflow.com",
        "full_name": "System Administrator",
        "hashed_password": get_password_hash("admin123"),
        "role": UserRole.ADMIN,
        "assigned_station_id": None,
        "is_active": True,
    }
}


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    email = login_data.email.lower()
    user_dict = DEMO_USERS.get(email)
    
    if not user_dict or not verify_password(login_data.password, user_dict["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_resp = UserResponse(
        id=user_dict["id"],
        email=user_dict["email"],
        full_name=user_dict["full_name"],
        role=user_dict["role"],
        assigned_station_id=user_dict["assigned_station_id"],
        is_active=user_dict["is_active"]
    )

    access_token = create_access_token(subject=user_dict["email"], roles=[user_dict["role"].value])
    refresh_token = create_refresh_token(subject=user_dict["email"], roles=[user_dict["role"].value])

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_resp
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    if user_in.email.lower() in DEMO_USERS:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    new_id = len(DEMO_USERS) + 1
    new_user = {
        "id": new_id,
        "email": user_in.email.lower(),
        "full_name": user_in.full_name,
        "hashed_password": get_password_hash(user_in.password),
        "role": user_in.role,
        "assigned_station_id": user_in.assigned_station_id,
        "is_active": True,
    }
    DEMO_USERS[user_in.email.lower()] = new_user

    return UserResponse(
        id=new_id,
        email=user_in.email,
        full_name=user_in.full_name,
        role=user_in.role,
        assigned_station_id=user_in.assigned_station_id,
        is_active=True
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    email = payload.get("sub")
    user_dict = DEMO_USERS.get(email)
    if not user_dict:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user_dict["id"],
        email=user_dict["email"],
        full_name=user_dict["full_name"],
        role=user_dict["role"],
        assigned_station_id=user_dict["assigned_station_id"],
        is_active=user_dict["is_active"]
    )
