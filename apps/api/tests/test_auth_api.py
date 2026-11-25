import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.v1 import auth as auth_routes
from app.core.security import hash_token
from app.db.dependencies import get_db
from app.main import app
from app.models import AuthSession, EmailOTPChallenge


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app, client=("198.51.100.10", 50000)) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def mock_email_delivery(monkeypatch):
    sent = {}

    def fake_send_otp_email(email, code):
        sent["email"] = email
        sent["code"] = code

    monkeypatch.setattr(
        auth_routes,
        "send_otp_email",
        fake_send_otp_email,
    )

    return sent


def authenticate_client(client, monkeypatch, email):
    sent = mock_email_delivery(monkeypatch)

    request_response = client.post(
        "/api/v1/auth/request-code",
        json={"email": email},
    )

    assert request_response.status_code == 200
    assert sent["email"] == email

    verify_response = client.post(
        "/api/v1/auth/verify-code",
        json={
            "email": email,
            "code": sent["code"],
        },
    )

    assert verify_response.status_code == 200

    return verify_response


def test_request_code_sends_email_and_stores_challenge(
    client,
    db_session,
    monkeypatch,
):
    email = "request-route@example.com"
    sent = mock_email_delivery(monkeypatch)

    response = client.post(
        "/api/v1/auth/request-code",
        json={"email": email},
    )

    assert response.status_code == 200
    assert "message" in response.json()
    assert sent["email"] == email
    assert len(sent["code"]) == 6
    assert sent["code"].isascii()
    assert sent["code"].isdigit()
    assert sent["code"] not in response.text

    challenge = db_session.scalar(
        select(EmailOTPChallenge).where(
            EmailOTPChallenge.email == email
        )
    )

    assert challenge is not None
    assert challenge.code_hash != sent["code"]
    assert len(challenge.code_hash) == 64


def test_verify_code_creates_session_and_sets_secure_cookies(
    client,
    monkeypatch,
):
    email = "verify-route@example.com"

    response = authenticate_client(
        client,
        monkeypatch,
        email,
    )
    data = response.json()

    assert data["user"]["email"] == email
    assert data["csrf_token"]

    set_cookie_headers = response.headers.get_list("set-cookie")

    session_cookie = next(
        (value for value in set_cookie_headers
         if value.startswith("soll_session=")),
        None,
    )
    csrf_cookie = next(
        (value for value in set_cookie_headers
         if value.startswith("soll_csrf=")),
        None,
    )

    assert session_cookie is not None
    assert csrf_cookie is not None

    assert "httponly" in session_cookie.lower()
    assert "httponly" not in csrf_cookie.lower()

    for cookie in (session_cookie, csrf_cookie):
        assert "path=/" in cookie.lower()
        assert "samesite=lax" in cookie.lower()

    assert client.cookies.get("soll_session")
    assert client.cookies.get("soll_csrf") == data["csrf_token"]

    me_response = client.get("/api/v1/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


def test_me_rejects_unauthenticated_request(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_logout_rejects_missing_and_mismatched_csrf(
    client,
    monkeypatch,
):
    authenticate_client(
        client,
        monkeypatch,
        "csrf-route@example.com",
    )

    missing_header = client.post("/api/v1/auth/logout")

    assert missing_header.status_code == 403

    mismatched_header = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": "incorrect-token"},
    )

    assert mismatched_header.status_code == 403


def test_logout_revokes_session_and_clears_cookies(
    client,
    db_session,
    monkeypatch,
):
    verify_response = authenticate_client(
        client,
        monkeypatch,
        "logout-route@example.com",
    )
    csrf_token = verify_response.json()["csrf_token"]

    session_token = client.cookies.get("soll_session")
    assert session_token

    auth_session = db_session.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == hash_token(session_token)
        )
    )

    assert auth_session is not None
    assert auth_session.revoked_at is None

    response = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200
    assert response.json()["message"]

    db_session.refresh(auth_session)
    assert auth_session.revoked_at is not None

    cleared_cookies = response.headers.get_list("set-cookie")

    for cookie_name in ("soll_session", "soll_csrf"):
        clearing_header = next(
            (value for value in cleared_cookies
             if value.startswith(f"{cookie_name}=")),
            None,
        )

        assert clearing_header is not None
        assert "max-age=0" in clearing_header.lower()

    me_response = client.get("/api/v1/auth/me")

    assert me_response.status_code == 401


def test_wrong_otp_attempt_is_persisted(
    client,
    db_session,
    monkeypatch,
):
    email = "wrong-code-route@example.com"
    sent = mock_email_delivery(monkeypatch)

    request_response = client.post(
        "/api/v1/auth/request-code",
        json={"email": email},
    )

    assert request_response.status_code == 200

    wrong_code = (
        "000000"
        if sent["code"] != "000000"
        else "999999"
    )

    verify_response = client.post(
        "/api/v1/auth/verify-code",
        json={
            "email": email,
            "code": wrong_code,
        },
    )

    assert verify_response.status_code == 401

    challenge = db_session.scalar(
        select(EmailOTPChallenge).where(
            EmailOTPChallenge.email == email
        )
    )

    assert challenge is not None
    assert challenge.attempt_count == 1
