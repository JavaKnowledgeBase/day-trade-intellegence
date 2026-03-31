"""Authentication helpers that support bearer tokens first and API-key fallback for local compatibility."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db_session
from app.core.settings import Settings, get_settings
from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.security.tokens import TokenManager


class UserRole(str):
    """Application roles used to protect endpoints with coarse-grained access control."""

    TRADER = "TRADER"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


def _resolve_role_from_api_key(api_key: str, settings: Settings) -> str | None:
    """Map the incoming API key to a configured application role."""
    if api_key == settings.admin_api_key:
        return UserRole.ADMIN
    if api_key == settings.operator_api_key:
        return UserRole.OPERATOR
    if api_key == settings.trader_api_key:
        return UserRole.TRADER
    return None


def _resolve_user_from_bearer_token(authorization: str | None, settings: Settings, user_repository: UserRepository) -> User | None:
    """Decode a bearer token and load the matching active user from the database."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    payload = TokenManager.decode_access_token(settings, token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    user = user_repository.get_by_username(username)
    if user is None or not user.is_active:
        return None
    return user


def require_role(allowed_roles: set[str]):
    """Create a dependency that validates bearer auth or API-key fallback and enforces allowed roles."""

    def dependency(
        session: Annotated[Session, Depends(get_db_session)],
        authorization: Annotated[str | None, Header(alias="Authorization")] = None,
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
        settings: Settings = Depends(get_settings),
    ) -> str:
        user_repository = UserRepository(session)
        user = _resolve_user_from_bearer_token(authorization, settings, user_repository)
        role = user.role if user else None
        if role is None and x_api_key:
            role = _resolve_role_from_api_key(x_api_key, settings)
        if role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid credentials.")
        if role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this endpoint.")
        return role

    return dependency
