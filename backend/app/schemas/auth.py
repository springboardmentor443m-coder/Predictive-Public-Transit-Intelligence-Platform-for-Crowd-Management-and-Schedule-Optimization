from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request payload for JWT token authentication."""
    username: str = Field(..., description="Operator or administrator username")
    password: str = Field(..., description="Account password")


class TokenResponse(BaseModel):
    """Response payload containing issued JWT access token."""
    access_token: str = Field(..., description="Signed JSON Web Token (Bearer)")
    token_type: str = Field("bearer", description="Token authentication scheme type")
    role: str = Field(..., description="Role assigned to the authenticated user ('admin' or 'operator')")
    username: str = Field(..., description="Username of the authenticated account")
