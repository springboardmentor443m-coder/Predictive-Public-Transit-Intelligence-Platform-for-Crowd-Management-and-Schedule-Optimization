from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


from app.schemas.user import UserResponse
Token.model_rebuild()
