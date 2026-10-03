import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Header, Response, status

from src.common.database import blocked_token_db, session_db, user_db
from src.auth.errors import InvalidAccountException, InvalidSessionException, InvalidTokenException, UnauthenticatedException
from src.auth.schemas import UserSignInRequest, TokenResponse
from src.auth.utils import (
    ACCESS_TOKEN_SECRET, REFRESH_TOKEN_SECRET, get_token_from_authorization_header,
    get_user_by_email, issue_token, verify_and_decode_token, verify_password,
)
from src.users.schemas import User

auth_router = APIRouter(prefix="/auth", tags=["auth"])

SHORT_SESSION_LIFESPAN = 15
LONG_SESSION_LIFESPAN = 24 * 60

def get_current_user(
    sid: Annotated[str | None, Cookie()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if sid is not None:
        record = session_db.get(sid)
        if record is None:
            raise InvalidSessionException()
        user_id, expires_at = record
        if expires_at <= int(datetime.now(timezone.utc).timestamp()):
            session_db.pop(sid, None)
            raise InvalidSessionException()
        user = next((u for u in user_db if u.user_id == user_id), None)
        if user is None:
            raise InvalidSessionException()
        return user
    if authorization is None:
        raise UnauthenticatedException()
    token = get_token_from_authorization_header(authorization)
    claims = verify_and_decode_token(token, ACCESS_TOKEN_SECRET)
    user = next((u for u in user_db if u.user_id == int(claims["sub"])), None)
    if user is None:
        raise InvalidTokenException()
    return user


def _authenticate(request: UserSignInRequest) -> User:
    user = get_user_by_email(request.email)
    if user is None:
        raise InvalidAccountException()
    verify_password(request.password, user.hashed_password)
    return user


def _new_tokens(user_id: int) -> TokenResponse:
    access, _ = issue_token(user_id, SHORT_SESSION_LIFESPAN, ACCESS_TOKEN_SECRET)
    refresh, _ = issue_token(user_id, LONG_SESSION_LIFESPAN, REFRESH_TOKEN_SECRET)
    return TokenResponse(access_token=access, refresh_token=refresh)


@auth_router.post("/token", status_code=status.HTTP_200_OK, response_model=TokenResponse)
def create_token(request: UserSignInRequest):
    user = _authenticate(request)
    return _new_tokens(user.user_id)


@auth_router.post("/token/refresh", status_code=status.HTTP_200_OK, response_model=TokenResponse)
def refresh_token(authorization: Annotated[str | None, Header()] = None):
    if authorization is None:
        raise UnauthenticatedException()
    token = get_token_from_authorization_header(authorization)
    if token in blocked_token_db:
        raise InvalidTokenException()
    claims = verify_and_decode_token(token, REFRESH_TOKEN_SECRET)
    user_id = int(claims["sub"])
    if not any(user.user_id == user_id for user in user_db):
        raise InvalidTokenException()
    blocked_token_db[token] = claims["exp"]
    return _new_tokens(user_id)


@auth_router.delete("/token", status_code=status.HTTP_204_NO_CONTENT)
def delete_token(authorization: Annotated[str | None, Header()] = None):
    if authorization is None:
        raise UnauthenticatedException()
    token = get_token_from_authorization_header(authorization)
    if token in blocked_token_db:
        raise InvalidTokenException()
    claims = verify_and_decode_token(token, REFRESH_TOKEN_SECRET)
    if not any(user.user_id == int(claims["sub"]) for user in user_db):
        raise InvalidTokenException()
    blocked_token_db[token] = claims["exp"]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.post("/session", status_code=status.HTTP_200_OK)
def create_session(request: UserSignInRequest, response: Response):
    user = _authenticate(request)
    sid = secrets.token_urlsafe(24)
    expires_at = int((datetime.now(timezone.utc) + timedelta(minutes=LONG_SESSION_LIFESPAN)).timestamp())
    session_db[sid] = (user.user_id, expires_at)
    response.set_cookie(
        key="sid", value=sid, httponly=True, samesite="lax",
        max_age=LONG_SESSION_LIFESPAN * 60,
    )


@auth_router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(response: Response, sid: Annotated[str | None, Cookie()] = None):
    if sid is not None:
        session_db.pop(sid, None)
        response.delete_cookie(key="sid")
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=response.headers)
