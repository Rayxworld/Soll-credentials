import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_otp_email(email: str, code: str) -> None:
    if not settings.smtp_host or not settings.smtp_from_email:
        raise RuntimeError("SMTP email delivery is not configured.")

    if settings.smtp_starttls and settings.smtp_ssl:
        raise RuntimeError("SMTP STARTTLS and SSL cannot both be enabled.")

    message = EmailMessage()
    message["Subject"] = "Your SOLL Credential sign-in code"
    message["From"] = settings.smtp_from_email
    message["To"] = email
    message.set_content(
        "Your SOLL Credential sign-in code is:\n\n"
        f"{code}\n\n"
        "This code expires in five minutes and can only be used once. "
        "If you did not request this code, you can ignore this email."
    )

    try:
        if settings.smtp_ssl:
            server_context = smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            )
        else:
            server_context = smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            )

        with server_context as server:
            server.ehlo()

            if settings.smtp_starttls and not settings.smtp_ssl:
                server.starttls()
                server.ehlo()

            if settings.smtp_username:
                if settings.smtp_password is None:
                    raise RuntimeError(
                        "SMTP password is required when username is configured."
                    )

                server.login(
                    settings.smtp_username,
                    settings.smtp_password.get_secret_value(),
                )

            server.send_message(message)

    except (smtplib.SMTPException, OSError) as exc:
        raise RuntimeError("Unable to deliver sign-in email.") from exc
