import hashlib
import hmac
import secrets
import uuid

from app.core.config import get_otp_pepper


def generate_otp() -> str:
    """Generate a cryptographically secure six-digit OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(email: str, challenge_id: uuid.UUID, code: str) -> str:
    """Hash an OTP using a server-side pepper and challenge context."""
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        raise ValueError("OTP must contain exactly six digits.")

    normalized_email = email.strip().casefold()

    message = (
        f"soll-credential:email-otp:v1:"
        f"{normalized_email}:{challenge_id}:{code}"
    ).encode("utf-8")

    pepper = get_otp_pepper().encode("utf-8")

    return hmac.new(pepper, message, hashlib.sha256).hexdigest()


def verify_otp(
    email: str,
    challenge_id: uuid.UUID,
    code: str,
    stored_hash: str,
) -> bool:
    """Verify an OTP hash using constant-time comparison."""
    try:
        candidate_hash = hash_otp(email, challenge_id, code)
    except ValueError:
        return False

    return hmac.compare_digest(candidate_hash, stored_hash)


def generate_session_token() -> str:
    """Generate a high-entropy opaque session token."""
    return secrets.token_urlsafe(32)


def generate_csrf_token() -> str:
    """Generate a high-entropy CSRF token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Return a SHA-256 hash for a high-entropy token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
