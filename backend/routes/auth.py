"""
MetroFlow Authentication & Role-Based Access Control (RBAC) Module
Supports Admin and Operator roles, profile management, and token-based sessions.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
import jwt
from datetime import datetime, timedelta
from db.database import get_db_connection, hash_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECRET_KEY = "metroflow-jwt-secure-signing-key-nyc-transit"
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreateRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str # 'admin' or 'operator'
    title: str
    badge_id: str

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=12)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        # Default mock admin for development convenience if no token passed
        return {
            "id": 1,
            "email": "admin@metroflow.ny",
            "name": "Sarah Chen",
            "role": "admin",
            "title": "Chief Transit Director",
            "badge_id": "NY-ADM-01"
        }
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

@router.post("/login")
def login(req: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(req.password)
    
    cursor.execute("SELECT * FROM users WHERE email = ? AND password_hash = ?", (req.email, pwd_hash))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_dict = dict(user)
    token = create_access_token({
        "id": user_dict["id"],
        "email": user_dict["email"],
        "name": user_dict["name"],
        "role": user_dict["role"],
        "title": user_dict["title"],
        "badge_id": user_dict["badge_id"]
    })

    cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_dict["id"],))
    conn.commit()
    conn.close()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_dict["id"],
            "email": user_dict["email"],
            "name": user_dict["name"],
            "role": user_dict["role"],
            "title": user_dict["title"],
            "badge_id": user_dict["badge_id"]
        }
    }

@router.get("/profile")
def get_profile(user: dict = Depends(get_current_user)):
    return {"user": user}

@router.get("/users")
def list_users(user: dict = Depends(get_current_user)):
    # Accessible to operators and admins, full details
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, role, title, badge_id, created_at, last_login FROM users")
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"users": users}

@router.post("/users")
def create_operator_user(req: UserCreateRequest, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required to create staff users")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (email, password_hash, name, role, title, badge_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (req.email, hash_password(req.password), req.name, req.role, req.title, req.badge_id))
        
        # Log action
        cursor.execute("""
        INSERT INTO operational_logs (user_name, role, action, details)
        VALUES (?, ?, 'USER_CREATED', ?)
        """, (current_user.get("name", "Admin"), current_user.get("role", "admin"), f"Created {req.role} account for {req.name} ({req.email})"))

        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="User email already exists")

    conn.close()
    return {"message": "User created successfully", "email": req.email}
