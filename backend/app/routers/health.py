from fastapi import APIRouter, Depends

from app.auth_utils import get_current_user


router = APIRouter()


@router.get("/health")
def health_check(
    current_user=Depends(get_current_user)
):
    return {
        "status": "healthy",
        "user": current_user.username
    }