"""Domain models used by the authentication and current-user flows."""

from datetime import datetime

from pydantic import BaseModel


class UserRead(BaseModel):
    """API model returned for authenticated user introspection."""

    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    """Request body accepted by the login endpoint."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Response body returned after a successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
