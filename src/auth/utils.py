import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError, VerificationError

from src.auth.errors import (
    BadAuthorizationHeaderException,
    InvalidAccountException,
    InvalidTokenException,
)
from src.common.database import user_db
from src.users.schemas import User

ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET") or secrets.token_urlsafe(32)
REFRESH_TOKEN_SECRET = os.environ.get("REFRESH_TOKEN_SECRET") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"


def get_user_by_email(email: str) -> User | None:
    return next((user for user in user_db if user.email == email), None)


def verify_password(plain_password: str, hashed_password: str) -> None:
    try:
        PasswordHasher().verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        raise InvalidAccountException()


def issue_token(user_id: int, lifespan_minutes: int, secret: str) -> tuple[str, int]:
    expires_at = int((datetime.now(timezone.utc) + timedelta(minutes=lifespan_minutes)).timestamp())
    token = jwt.encode(
        {"sub": str(user_id), "exp": expires_at, "jti": secrets.token_urlsafe(16)},
        secret,
        algorithm=ALGORITHM,
    )
    return token, expires_at


def verify_and_decode_token(token: str, secret: str) -> dict:
    try:
        claims = jwt.decode(
            token, secret, algorithms=[ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        if not isinstance(claims.get("sub"), str) or not claims["sub"].isdigit():
            raise InvalidTokenException()
        return claims
    except InvalidTokenException:
        raise
    except (jwt.PyJWTError, TypeError, ValueError):
        raise InvalidTokenException()


def get_token_from_authorization_header(authorization: str) -> str:
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise BadAuthorizationHeaderException()
    return parts[1]
