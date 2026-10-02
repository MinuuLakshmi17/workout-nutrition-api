from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

try:
    from pwdlib import PasswordHash

    _password = PasswordHash.recommended()

    def hash_password(password):
        return _password.hash(password)

    def verify_password(password, hashed):
        return _password.verify(password, hashed)

except ImportError:
    from argon2 import PasswordHasher

    _password = PasswordHasher()

    def hash_password(password):
        return _password.hash(password)

    def verify_password(password, hashed):
        try:
            return _password.verify(hashed, password)
        except Exception:
            return False


from app.core.config import settings


def create_access_token(subject):
    exp = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": str(subject), "exp": exp},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token):
    try:
        sub = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        ).get("sub")
        if not sub:
            raise ValueError
        return int(sub)
    except Exception as e:
        raise ValueError("Invalid token") from e


def create_refresh_token(subject):
    """Issue a refresh token and return (token, jti).

    The jti must be stored server-side (Redis allowlist) so a stolen or
    logged-out token can be revoked before its natural expiry.
    """
    jti = uuid4().hex
    exp = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    token = jwt.encode(
        {"sub": str(subject), "type": "refresh", "jti": jti, "exp": exp},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, jti


def decode_refresh_token(token):
    """Return (user_id, jti) for a valid refresh token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != "refresh" or not payload.get("jti"):
            raise ValueError
        return int(payload["sub"]), payload["jti"]
    except Exception as e:
        raise ValueError("Invalid refresh token") from e
