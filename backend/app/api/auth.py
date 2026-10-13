from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

router = APIRouter(prefix="/api/auth", tags=["Auth"])

SECRET_KEY = "METROFLOW_OPERATIONAL_SECRET"
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str

@router.post("/login")
def login(request: LoginRequest):
    valid_roles = ["ADMIN", "OPERATOR"]
    if request.role.upper() not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role assigned"
        )

    # Allows any user / email as long as password is provided
    if not request.username.strip() or not request.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Station ID / Email and Key cannot be empty"
        )

    # Generate JWT Claims
    payload = {
        "sub": request.username,
        "role": request.role.upper(),
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": request.username,
            "role": request.role.upper(),
            "station_access": "ALL"
        }
    }