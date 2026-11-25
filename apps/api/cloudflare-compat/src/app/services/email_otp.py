import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from app.core.security import generate_otp, hash_otp, verify_otp
from app.models import EmailOTPChallenge, User


OTP_TTL = timedelta(minutes=5)
OTP_RESEND_COOLDOWN = timedelta(seconds=60)
OTP_MAX_REQUESTS_PER_DAY = 10
OTP_MAX_ATTEMPTS = 5


@dataclass(frozen=True)
class OTPDispatch:
    """Internal delivery data. Never serialize this object in an API response."""

    challenge_id: uuid.UUID
    email: str
    code: str


@dataclass(frozen=True)
class OTPVerification:
    """Result of OTP verification."""

    success: bool
    user: User | None = None


def normalize_email(email: str) -> str:
    try:
        result = validate_email(
            email.strip(),
            check_deliverability=False,
        )
    except EmailNotValidError:
        raise ValueError("Invalid email address.")

    return result.normalized.casefold()


def _email_lock_key(email: str) -> int:
    digest = hashlib.sha256(
        f"soll-credential:otp-request:v1:{email}".encode("utf-8")
    ).digest()

    return int.from_bytes(digest[:8], byteorder="big", signed=True)


def _lock_email(db: Session, email: str) -> None:
    db.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": _email_lock_key(email)},
    )


def request_email_otp(db: Session, email: str) -> OTPDispatch:
    """Create a challenge. Caller owns the transaction and email delivery."""

    normalized_email = normalize_email(email)
    now = datetime.now(timezone.utc)

    _lock_email(db, normalized_email)

    latest = db.scalar(
        select(EmailOTPChallenge)
        .where(EmailOTPChallenge.email == normalized_email)
        .order_by(EmailOTPChallenge.created_at.desc())
        .limit(1)
    )

    if latest is not None:
        latest_created_at = latest.created_at

        if latest_created_at.tzinfo is None:
            latest_created_at = latest_created_at.replace(
                tzinfo=timezone.utc
            )

        if now - latest_created_at < OTP_RESEND_COOLDOWN:
            raise ValueError("Please wait before requesting another code.")

    requests_today = db.scalar(
        select(func.count())
        .select_from(EmailOTPChallenge)
        .where(
            EmailOTPChallenge.email == normalized_email,
            EmailOTPChallenge.created_at >= now - timedelta(days=1),
        )
    ) or 0

    if requests_today >= OTP_MAX_REQUESTS_PER_DAY:
        raise ValueError("Too many code requests. Try again later.")

    db.execute(
        update(EmailOTPChallenge)
        .where(
            EmailOTPChallenge.email == normalized_email,
            EmailOTPChallenge.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )

    challenge_id = uuid.uuid4()
    code = generate_otp()

    challenge = EmailOTPChallenge(
        id=challenge_id,
        email=normalized_email,
        code_hash=hash_otp(normalized_email, challenge_id, code),
        expires_at=now + OTP_TTL,
    )

    db.add(challenge)
    db.flush()

    return OTPDispatch(
        challenge_id=challenge_id,
        email=normalized_email,
        code=code,
    )


def verify_email_otp(
    db: Session,
    email: str,
    code: str,
) -> OTPVerification:
    """
    Verify the latest active challenge.

    Failed attempts are flushed, not rolled back. The API layer must commit
    the transaction before returning an authentication failure.
    """

    normalized_email = normalize_email(email)
    now = datetime.now(timezone.utc)

    _lock_email(db, normalized_email)

    challenge = db.scalar(
        select(EmailOTPChallenge)
        .where(
            EmailOTPChallenge.email == normalized_email,
            EmailOTPChallenge.consumed_at.is_(None),
        )
        .order_by(EmailOTPChallenge.created_at.desc())
        .limit(1)
        .with_for_update()
    )

    if challenge is None:
        return OTPVerification(success=False)

    expires_at = challenge.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now or challenge.attempt_count >= OTP_MAX_ATTEMPTS:
        challenge.consumed_at = now
        db.flush()
        return OTPVerification(success=False)

    if not verify_otp(
        normalized_email,
        challenge.id,
        code,
        challenge.code_hash,
    ):
        challenge.attempt_count += 1

        if challenge.attempt_count >= OTP_MAX_ATTEMPTS:
            challenge.consumed_at = now

        db.flush()
        return OTPVerification(success=False)

    challenge.consumed_at = now

    user = db.scalar(
        select(User)
        .where(func.lower(User.email) == normalized_email)
        .with_for_update()
    )

    if user is None:
        user = User(
            email=normalized_email,
            email_verified_at=now,
        )
        db.add(user)
    elif not user.is_active:
        db.flush()
        return OTPVerification(success=False)
    elif user.email_verified_at is None:
        user.email_verified_at = now

    db.flush()

    return OTPVerification(
        success=True,
        user=user,
    )
