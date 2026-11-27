import logging

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)

RESEND_EMAILS_URL = "https://api.resend.com/emails"


def send_otp_email(email: str, code: str) -> None:
    """Deliver a one-time sign-in code through Resend's HTTPS API.

    HTTPS is used instead of SMTP because some hosting environments block
    outbound SMTP ports. Never log the recipient, OTP, API key, or response
    body: provider errors can contain sensitive request details.
    """
    if settings.resend_api_key is None or not settings.resend_from_email:
        raise RuntimeError("Resend email delivery is not configured.")

    message = {
        "from": settings.resend_from_email,
        "to": [email],
        "subject": "Your SOLL Credential sign-in code",
        "text": (
            "Your SOLL Credential sign-in code is:\n\n"
            f"{code}\n\n"
            "This code expires in five minutes and can only be used once. "
            "If you did not request this code, you can ignore this email."
        ),
    }

    try:
        response = httpx.post(
            RESEND_EMAILS_URL,
            headers={
                "Authorization": (
                    f"Bearer {settings.resend_api_key.get_secret_value()}"
                ),
                "Content-Type": "application/json",
            },
            json=message,
            timeout=settings.resend_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        response = getattr(exc, "response", None)
        status_code = response.status_code if response is not None else None
        logger.error(
            "Resend email delivery failed (exception_type=%s, http_status=%s)",
            type(exc).__name__,
            status_code,
        )
        raise RuntimeError("Unable to deliver sign-in email.") from exc
