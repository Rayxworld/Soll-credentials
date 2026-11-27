import httpx
import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.services import email_delivery


def configure_resend(monkeypatch):
    monkeypatch.setattr(
        settings,
        "resend_api_key",
        SecretStr("test-resend-api-key"),
    )
    monkeypatch.setattr(
        settings,
        "resend_from_email",
        "onboarding@resend.dev",
    )
    monkeypatch.setattr(settings, "resend_timeout_seconds", 15)


def test_send_otp_email_uses_resend_https_api(monkeypatch):
    configure_resend(monkeypatch)
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return httpx.Response(
            200,
            json={"id": "email-test-id"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(email_delivery.httpx, "post", fake_post)

    email_delivery.send_otp_email("recipient@example.com", "123456")

    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["headers"]["Authorization"] == "Bearer test-resend-api-key"
    assert captured["json"]["from"] == "onboarding@resend.dev"
    assert captured["json"]["to"] == ["recipient@example.com"]
    assert "123456" in captured["json"]["text"]
    assert captured["timeout"] == 15


def test_send_otp_email_rejects_missing_configuration(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", None)
    monkeypatch.setattr(
        settings,
        "resend_from_email",
        "onboarding@resend.dev",
    )

    with pytest.raises(RuntimeError, match="not configured"):
        email_delivery.send_otp_email("recipient@example.com", "123456")


def test_send_otp_email_logs_status_without_sensitive_data(
    monkeypatch,
    caplog,
):
    configure_resend(monkeypatch)

    def fake_post(url, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(
            403,
            text="provider response containing sensitive details",
            request=request,
        )

    monkeypatch.setattr(email_delivery.httpx, "post", fake_post)

    with pytest.raises(RuntimeError, match="Unable to deliver"):
        email_delivery.send_otp_email("recipient@example.com", "123456")

    assert "http_status=403" in caplog.text
    assert "test-resend-api-key" not in caplog.text
    assert "recipient@example.com" not in caplog.text
    assert "123456" not in caplog.text
    assert "provider response containing sensitive details" not in caplog.text
