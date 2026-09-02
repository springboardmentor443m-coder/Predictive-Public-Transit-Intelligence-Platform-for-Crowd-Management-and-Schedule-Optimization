"""
Milestone 1 - User Management Module
- Admin/operator login
- Role-based access control
- JWT-based auth
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = "metroflow-dev-secret-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# --- Demo user store (swap for a real DB table in production) ---
# Roles: "admin" (full access), "operator" (station-level monitoring only)
_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": _hash_password("admin123"),
        "role": "admin",
        "full_name": "Platform Administrator",
    },
    "operator1": {
        "username": "operator1",
        "hashed_password": _hash_password("operator123"),
        "role": "operator",
        "full_name": "Station Operator",
        "assigned_station": "Taipei Main Station",
    },
}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    username: str
    role: str
    full_name: str
    assigned_station: Optional[str] = None


def authenticate_user(username: str, password: str):
    user = _USERS_DB.get(username)
    if not user or not _verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserProfile:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = _USERS_DB.get(username)
    if user is None:
        raise credentials_exception
    return UserProfile(
        username=user["username"],
        role=user["role"],
        full_name=user["full_name"],
        assigned_station=user.get("assigned_station"),
    )


def require_admin(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
