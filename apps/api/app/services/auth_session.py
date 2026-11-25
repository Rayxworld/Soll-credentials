import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    generate_csrf_token,
    generate_session_token,
    hash_token,
)
from app.models import AuthSession, User


@dataclass(frozen=True)
class CreatedAuthSession:
    session: AuthSession
    session_token: str
    csrf_token: str


def create_auth_session(
    db: Session,
    user: User,
) -> CreatedAuthSession:
    if not user.is_active or user.email_verified_at is None:
        raise ValueError("User is not eligible for authentication.")

    now = datetime.now(timezone.utc)
    session_token = generate_session_token()
    csrf_token = generate_csrf_token()

    auth_session = AuthSession(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_token(session_token),
        csrf_token_hash=hash_token(csrf_token),
        expires_at=now + timedelta(days=settings.session_ttl_days),
    )

    db.add(auth_session)
    db.flush()

    return CreatedAuthSession(
        session=auth_session,
        session_token=session_token,
        csrf_token=csrf_token,
    )


def get_valid_auth_session(
    db: Session,
    session_token: str,
) -> AuthSession | None:
    if not session_token:
        return None

    auth_session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == hash_token(session_token),
            AuthSession.revoked_at.is_(None),
        )
    )

    if auth_session is None:
        return None

    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        return None

    return auth_session


def revoke_auth_session(
    db: Session,
    auth_session: AuthSession,
) -> None:
    if auth_session.revoked_at is None:
        auth_session.revoked_at = datetime.now(timezone.utc)
        db.flush()


def revoke_all_user_sessions(
    db: Session,
    user_id: uuid.UUID,
) -> int:
    result = db.execute(
        update(AuthSession)
        .where(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    return result.rowcount or 0
