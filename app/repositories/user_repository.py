"""Repository used to persist and query local template users."""

from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    """Encapsulate local user lookups and inserts so auth logic stays out of route handlers."""

    def __init__(self, session: Session) -> None:
        """Store the SQLAlchemy session used for user queries and writes."""
        self.session = session

    def get_by_username(self, username: str) -> User | None:
        """Return one user by username or None when the user does not exist."""
        return self.session.query(User).filter(User.username == username).one_or_none()

    def create_user(self, username: str, password_hash: str, role: str, is_active: bool = True) -> User:
        """Insert one local template user and commit it immediately."""
        user = User(username=username, password_hash=password_hash, role=role, is_active=is_active)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
