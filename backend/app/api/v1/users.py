import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import ProfileUpdate, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/me", response_model=UserRead)
async def update_own_profile(
    profile_in: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if profile_in.full_name is not None:
        if not profile_in.full_name.strip():
            raise HTTPException(status_code=422, detail="Full name cannot be empty")
        current_user.full_name = profile_in.full_name.strip()
    if profile_in.password is not None:
        current_user.hashed_password = hash_password(profile_in.password)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("", response_model=list[UserRead])
async def list_users(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    return db.query(User).all()


@router.post("", response_model=UserRead)
async def create_user(user_in: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        id=str(uuid.uuid4()),
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: str, user_in: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_in.email is not None:
        clash = db.query(User).filter(User.email == user_in.email, User.id != user.id).first()
        if clash:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = user_in.email
    if user_in.full_name is not None:
        if not user_in.full_name.strip():
            raise HTTPException(status_code=422, detail="Full name cannot be empty")
        user.full_name = user_in.full_name.strip()
    if user_in.role is not None:
        allowed_roles = {"admin", "operator", "viewer"}
        if user_in.role not in allowed_roles:
            raise HTTPException(status_code=422, detail=f"Role must be one of: {', '.join(sorted(allowed_roles))}")
        user.role = user_in.role
    if user_in.password is not None:
        user.hashed_password = hash_password(user_in.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(user_id: str, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
