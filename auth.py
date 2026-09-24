import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from passlib.context import CryptContext

# --- Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "metroflow-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# --- Auth Functions ---
async def authenticate_user(username: str, password: str, session: AsyncSession) -> Optional[dict]:
    user = await get_user_by_username(username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "access_token": create_access_token({"sub": user.username, "role": user.role})
    }

async def ensure_default_admin(session: AsyncSession):
    """Create default admin on first startup."""
    admin = await get_user_by_username("admin")
    if not admin:
        await create_user("admin", hash_password("admin123"), "admin", session)
        print("Default admin created: admin / admin123")

async def get_current_user(token: str, session: AsyncSession) -> Optional["User"]:
    payload = decode_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    return await get_user_by_username(username)

async def get_user_by_username(username: str) -> Optional["User"]:
    from database import User, async_session
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

async def create_user(username: str, password_hash: str, role: str, session: AsyncSession) -> "User":
    from database import User
    user = User(username=username, password_hash=password_hash, role=role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
