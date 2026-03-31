"""Service used to authenticate users and issue signed bearer tokens."""

from app.core.errors import ConfigurationError
from app.core.settings import Settings
from app.domain.auth import TokenResponse, UserRead
from app.repositories.user_repository import UserRepository
from app.security.tokens import PasswordManager, TokenManager


class AuthService:
    """Authenticate local users against stored password hashes and issue signed access tokens."""

    def __init__(self, settings: Settings, user_repository: UserRepository) -> None:
        """Store the runtime auth settings and repository used by login and user lookup flows."""
        self.settings = settings
        self.user_repository = user_repository

    def login(self, username: str, password: str) -> TokenResponse:
        """Validate credentials and return a signed bearer token with basic user details."""
        user = self.user_repository.get_by_username(username)
        if user is None or not user.is_active:
            raise ConfigurationError("Invalid username or password.")
        if not PasswordManager.verify_password(password, user.password_hash):
            raise ConfigurationError("Invalid username or password.")
        token, expires_in = TokenManager.create_access_token(self.settings, subject=user.username, role=user.role)
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=UserRead(id=user.id, username=user.username, role=user.role, is_active=user.is_active, created_at=user.created_at),
        )

    def get_user(self, username: str) -> UserRead | None:
        """Return one local user as an API model for authenticated introspection flows."""
        user = self.user_repository.get_by_username(username)
        if user is None:
            return None
        return UserRead(id=user.id, username=user.username, role=user.role, is_active=user.is_active, created_at=user.created_at)
