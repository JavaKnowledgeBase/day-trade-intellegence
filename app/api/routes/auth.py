"""Authentication endpoints for local user login and current-user introspection."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_auth_service, get_db_session
from app.core.settings import get_settings
from app.domain.auth import LoginRequest, TokenResponse, UserRead
from app.repositories.user_repository import UserRepository
from app.security.tokens import TokenManager
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    request: LoginRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> TokenResponse:
    """Validate local user credentials and return a signed bearer token."""
    auth_service: AuthService = get_auth_service(session)
    return auth_service.login(request.username, request.password)


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_current_user(
    session: Annotated[Session, Depends(get_db_session)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> UserRead:
    """Return the current authenticated user derived from the bearer token."""
    settings = get_settings()
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")
    payload = TokenManager.decode_access_token(settings, authorization.removeprefix("Bearer ").strip())
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token.")
    user = UserRepository(session).get_by_username(str(payload.get("sub", "")))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user not found.")
    return UserRead(id=user.id, username=user.username, role=user.role, is_active=user.is_active, created_at=user.created_at)
