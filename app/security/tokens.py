"""Password hashing and signed bearer-token helpers implemented with the Python standard library."""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta

from app.core.settings import Settings


class PasswordManager:
    """Hash and verify passwords using PBKDF2 so the runnable template avoids plain-text credentials."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password with a random salt and return a compact storage string."""
        salt = secrets.token_hex(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 150000)
        return f"{salt}${derived.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against a stored PBKDF2 hash string."""
        try:
            salt, expected = password_hash.split("$", maxsplit=1)
        except ValueError:
            return False
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 150000)
        return hmac.compare_digest(derived.hex(), expected)


class TokenManager:
    """Create and verify compact signed bearer tokens with JWT-like semantics using stdlib primitives."""

    @staticmethod
    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _b64url_decode(data: str) -> bytes:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode((data + padding).encode("utf-8"))

    @classmethod
    def create_access_token(cls, settings: Settings, subject: str, role: str) -> tuple[str, int]:
        """Create a signed bearer token containing subject, role, and expiration claims."""
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.auth_token_exp_minutes)
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": subject, "role": role, "exp": int(expires_at.timestamp())}
        signing_input = f"{cls._b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))}.{cls._b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))}"
        signature = hmac.new(settings.auth_secret_key.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
        token = f"{signing_input}.{cls._b64url_encode(signature)}"
        return token, settings.auth_token_exp_minutes * 60

    @classmethod
    def decode_access_token(cls, settings: Settings, token: str) -> dict | None:
        """Validate a signed token and return its payload when it is authentic and unexpired."""
        try:
            header_part, payload_part, signature_part = token.split(".")
            signing_input = f"{header_part}.{payload_part}"
            expected_signature = hmac.new(settings.auth_secret_key.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
            if not hmac.compare_digest(cls._b64url_encode(expected_signature), signature_part):
                return None
            payload = json.loads(cls._b64url_decode(payload_part).decode("utf-8"))
            if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
                return None
            return payload
        except Exception:
            return None
