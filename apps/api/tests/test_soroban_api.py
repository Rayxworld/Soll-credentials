from datetime import datetime, timezone
import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import soroban as soroban_api
from app.db.dependencies import get_db
from app.main import app
from app.models import Organization, OrganizationMembership, User
from app.services.auth_session import create_auth_session
from app.services.soroban import SorobanNotConfiguredError


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app, client=("198.51.100.21", 50000)) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def authenticate(db_session, client):
    user = User(
        email=f"{uuid.uuid4().hex}@example.com",
        email_verified_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.flush()
    session = create_auth_session(db_session, user)
    db_session.commit()
    client.cookies.set("soll_session", session.session_token)
    return user


def add_org(db_session, user, *, chain_id=None):
    organization = Organization(
        name="SOLL Network",
        slug=uuid.uuid4().hex,
        on_chain_org_id=chain_id,
        stellar_owner_address="GAMCAA5W2JQ5E4ZVHTRGNJW5E6EPJNWJ6DH6XQ6EB34GC2OYFHATUZNR",
        custody_mode="external",
    )
    db_session.add(organization)
    db_session.flush()
    db_session.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            role="owner",
            is_active=True,
        )
    )
    db_session.flush()
    return organization


def test_public_credential_status_returns_only_chain_metadata(client, monkeypatch):
    monkeypatch.setattr(
        soroban_api,
        "get_credential_record",
        lambda credential_id: {
            "organization_id": bytes.fromhex("11" * 32),
            "commitment": bytes.fromhex("22" * 32),
            "issuer": "GCJ22TNGAVLGOEI6OS4RUUK2KPLYQFDGRPNXTZH2YJCAH3DBWWESEMD2",
            "issued_at": 1_795_695_073,
            "revoked": False,
        },
    )

    response = client.get(f"/api/v1/public/credentials/{'aa' * 32}")

    assert response.status_code == 200
    body = response.json()
    assert body["credential_id"] == "aa" * 32
    assert body["organization_id"] == "11" * 32
    assert body["commitment"] == "22" * 32
    assert body["revoked"] is False
    assert "holder_name" not in body
    assert "email" not in body


def test_public_credential_status_returns_404_when_missing(client, monkeypatch):
    monkeypatch.setattr(soroban_api, "get_credential_record", lambda _: None)

    response = client.get(f"/api/v1/public/credentials/{'bb' * 32}")

    assert response.status_code == 404


def test_public_credential_status_rejects_malformed_id(client):
    response = client.get("/api/v1/public/credentials/not-a-credential-id")
    assert response.status_code == 422


def test_public_credential_status_reports_unconfigured_chain(client, monkeypatch):
    def unavailable(_):
        raise SorobanNotConfiguredError()

    monkeypatch.setattr(soroban_api, "get_credential_record", unavailable)
    response = client.get(f"/api/v1/public/credentials/{'cc' * 32}")
    assert response.status_code == 503


def test_issuer_authorization_requires_membership(client, db_session, monkeypatch):
    user = authenticate(db_session, client)
    organization = add_org(db_session, user, chain_id=bytes.fromhex("33" * 32))
    monkeypatch.setattr(soroban_api, "is_issuer_authorized", lambda *_: True)

    issuer = "GCJ22TNGAVLGOEI6OS4RUUK2KPLYQFDGRPNXTZH2YJCAH3DBWWESEMD2"
    response = client.get(
        f"/api/v1/organizations/{organization.id}/issuers/{issuer}/authorization"
    )

    assert response.status_code == 200
    assert response.json()["authorized"] is True


def test_issuer_authorization_hides_other_tenants(client, db_session, monkeypatch):
    other_user = User(
        email=f"{uuid.uuid4().hex}@example.com",
        email_verified_at=datetime.now(timezone.utc),
    )
    db_session.add(other_user)
    db_session.flush()
    organization = add_org(db_session, other_user, chain_id=bytes.fromhex("44" * 32))
    monkeypatch.setattr(soroban_api, "is_issuer_authorized", lambda *_: True)

    issuer = "GCJ22TNGAVLGOEI6OS4RUUK2KPLYQFDGRPNXTZH2YJCAH3DBWWESEMD2"
    response = client.get(
        f"/api/v1/organizations/{organization.id}/issuers/{issuer}/authorization"
    )

    assert response.status_code == 401
