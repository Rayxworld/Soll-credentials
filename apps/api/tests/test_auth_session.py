from datetime import datetime, timedelta, timezone

from app.core.security import hash_token
from app.models import AuthSession, User
from app.services.auth_session import (
    create_auth_session,
    get_valid_auth_session,
    revoke_all_user_sessions,
    revoke_auth_session,
)


def create_verified_user(db_session, email="session@example.com"):
    user = User(
        email=email,
        email_verified_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_create_auth_session_stores_only_token_hash(db_session):
    user = create_verified_user(db_session)

    created = create_auth_session(db_session, user)

    assert created.session_token
    assert created.csrf_token
    assert created.session.token_hash == hash_token(
        created.session_token
    )
    assert created.session.token_hash != created.session_token
    assert created.session.csrf_token_hash == hash_token(
        created.csrf_token
    )


def test_get_valid_auth_session(db_session):
    user = create_verified_user(db_session)
    created = create_auth_session(db_session, user)

    result = get_valid_auth_session(
        db_session,
        created.session_token,
    )

    assert result is not None
    assert result.id == created.session.id


def test_get_valid_auth_session_rejects_unknown_token(db_session):
    result = get_valid_auth_session(
        db_session,
        "not-a-valid-session-token",
    )

    assert result is None


def test_revoked_session_is_rejected(db_session):
    user = create_verified_user(db_session)
    created = create_auth_session(db_session, user)

    revoke_auth_session(db_session, created.session)

    result = get_valid_auth_session(
        db_session,
        created.session_token,
    )

    assert result is None


def test_expired_session_is_rejected(db_session):
    user = create_verified_user(db_session)
    created = create_auth_session(db_session, user)

    now = datetime.now(timezone.utc)
    created.session.created_at = now - timedelta(minutes=2)
    created.session.expires_at = now - timedelta(seconds=1)
    db_session.flush()

    result = get_valid_auth_session(
        db_session,
        created.session_token,
    )

    assert result is None


def test_revoke_all_user_sessions(db_session):
    user = create_verified_user(db_session)

    first = create_auth_session(db_session, user)
    second = create_auth_session(db_session, user)

    count = revoke_all_user_sessions(db_session, user.id)

    assert count == 2
    assert get_valid_auth_session(
        db_session,
        first.session_token,
    ) is None
    assert get_valid_auth_session(
        db_session,
        second.session_token,
    ) is None


def test_unverified_user_cannot_receive_session(db_session):
    user = User(
        email="unverified@example.com",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    try:
        create_auth_session(db_session, user)
        assert False, "Expected unverified user to be rejected."
    except ValueError:
        pass


def test_inactive_user_cannot_receive_session(db_session):
    user = User(
        email="disabled@example.com",
        email_verified_at=datetime.now(timezone.utc),
        is_active=False,
    )
    db_session.add(user)
    db_session.flush()

    try:
        create_auth_session(db_session, user)
        assert False, "Expected inactive user to be rejected."
    except ValueError:
        pass
