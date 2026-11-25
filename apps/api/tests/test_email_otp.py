import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import select, update

from app.core.security import verify_otp
from app.models import EmailOTPChallenge
from app.services.email_otp import request_email_otp


def test_request_email_otp_creates_hashed_challenge(db_session):
    dispatch = request_email_otp(db_session, " Test@Example.com ")
    challenge = db_session.get(EmailOTPChallenge, dispatch.challenge_id)

    assert dispatch.email == "test@example.com"
    assert len(dispatch.code) == 6
    assert challenge is not None
    assert challenge.code_hash != dispatch.code
    assert verify_otp(
        dispatch.email,
        dispatch.challenge_id,
        dispatch.code,
        challenge.code_hash,
    )
    assert challenge.expires_at > datetime.now(timezone.utc)


def test_request_email_otp_enforces_resend_cooldown(db_session):
    request_email_otp(db_session, "cooldown@example.com")

    with pytest.raises(ValueError) as exc_info:
        request_email_otp(db_session, "cooldown@example.com")

    assert 'wait' in str(exc_info.value).lower() or 'too many' in str(exc_info.value).lower()


def test_new_request_invalidates_previous_challenge(db_session):
    first = request_email_otp(db_session, "replace@example.com")

    db_session.execute(
        update(EmailOTPChallenge)
        .where(EmailOTPChallenge.id == first.challenge_id)
        .values(created_at=datetime.now(timezone.utc) - timedelta(seconds=61))
    )

    second = request_email_otp(db_session, "replace@example.com")

    old_challenge = db_session.get(EmailOTPChallenge, first.challenge_id)
    new_challenge = db_session.get(EmailOTPChallenge, second.challenge_id)

    assert old_challenge.consumed_at is not None
    assert new_challenge.consumed_at is None
    assert first.challenge_id != second.challenge_id


def test_request_email_otp_enforces_daily_limit(db_session):
    now = datetime.now(timezone.utc)

    for index in range(10):
        db_session.add(
            EmailOTPChallenge(
                id=uuid.uuid4(),
                email="limit@example.com",
                code_hash="a" * 64,
                expires_at=now + timedelta(minutes=5),
                created_at=now - timedelta(minutes=2 + index),
            )
        )

    db_session.flush()

    with pytest.raises(ValueError) as exc_info:
        request_email_otp(db_session, "limit@example.com")

    assert 'wait' in str(exc_info.value).lower() or 'too many' in str(exc_info.value).lower()

from app.core.security import hash_otp
from app.models import User
from app.services.email_otp import verify_email_otp


def create_challenge(db_session, email, code="123456", expires_in=300):
    challenge_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    challenge = EmailOTPChallenge(
        id=challenge_id,
        email=email,
        code_hash=hash_otp(email, challenge_id, code),
        expires_at=now + timedelta(seconds=expires_in),
    )

    db_session.add(challenge)
    db_session.flush()

    return challenge


def test_verify_email_otp_creates_verified_user(db_session):
    create_challenge(db_session, "newuser@example.com")

    result = verify_email_otp(
        db_session,
        "newuser@example.com",
        "123456",
    )

    assert result.success is True
    assert result.user is not None
    assert result.user.email == "newuser@example.com"
    assert result.user.email_verified_at is not None

    challenge = db_session.scalar(
        select(EmailOTPChallenge).where(
            EmailOTPChallenge.email == "newuser@example.com"
        )
    )
    assert challenge.consumed_at is not None


def test_verify_email_otp_rejects_wrong_code_and_counts_attempt(db_session):
    challenge = create_challenge(db_session, "wrong@example.com")

    result = verify_email_otp(
        db_session,
        "wrong@example.com",
        "999999",
    )

    db_session.refresh(challenge)

    assert result.success is False
    assert challenge.attempt_count == 1
    assert challenge.consumed_at is None


def test_verify_email_otp_consumes_after_five_failures(db_session):
    challenge = create_challenge(db_session, "locked@example.com")

    for _ in range(5):
        result = verify_email_otp(
            db_session,
            "locked@example.com",
            "999999",
        )
        assert result.success is False

    db_session.refresh(challenge)

    assert challenge.attempt_count == 5
    assert challenge.consumed_at is not None


def test_verify_email_otp_rejects_expired_challenge(db_session):
    challenge = create_challenge(
        db_session,
        "expired@example.com",
        expires_in=-1,
    )

    result = verify_email_otp(
        db_session,
        "expired@example.com",
        "123456",
    )

    db_session.refresh(challenge)

    assert result.success is False
    assert challenge.consumed_at is not None


def test_verify_email_otp_rejects_inactive_user(db_session):
    user = User(
        email="inactive@example.com",
        is_active=False,
    )
    db_session.add(user)
    db_session.flush()

    challenge = create_challenge(
        db_session,
        "inactive@example.com",
    )

    result = verify_email_otp(
        db_session,
        "inactive@example.com",
        "123456",
    )

    db_session.refresh(challenge)

    assert result.success is False
    assert challenge.consumed_at is not None
    assert user.email_verified_at is None


def test_verify_email_otp_cannot_replay_consumed_challenge(db_session):
    challenge = create_challenge(db_session, "replay@example.com")

    first = verify_email_otp(
        db_session,
        "replay@example.com",
        "123456",
    )
    second = verify_email_otp(
        db_session,
        "replay@example.com",
        "123456",
    )

    assert first.success is True
    assert second.success is False
