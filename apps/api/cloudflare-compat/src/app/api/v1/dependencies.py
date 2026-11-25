import hmac
from dataclasses import dataclass

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_token
from app.db.dependencies import get_db
from app.models import AuthSession, User
from app.services.auth_session import get_valid_auth_session


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: AuthSession


async def get_current_auth(
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(
        default=None,
        alias=settings.session_cookie_name,
    ),
) -> AuthContext:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    auth_session = get_valid_auth_session(db, session_token)

    if auth_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    user = db.scalar(
        select(User).where(User.id == auth_session.user_id)
    )

    if (
        user is None
        or not user.is_active
        or user.email_verified_at is None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not eligible for authentication.",
        )

    return AuthContext(user=user, session=auth_session)


async def require_csrf(
    auth: AuthContext = Depends(get_current_auth),
    csrf_header: str | None = Header(
        default=None,
        alias="X-CSRF-Token",
    ),
    csrf_cookie: str | None = Cookie(
        default=None,
        alias=settings.csrf_cookie_name,
    ),
) -> AuthContext:
    if not csrf_header or not csrf_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed.",
        )

    if not hmac.compare_digest(csrf_header, csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed.",
        )

    candidate_hash = hash_token(csrf_header)

    if not hmac.compare_digest(
        candidate_hash,
        auth.session.csrf_token_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed.",
        )

    return auth
