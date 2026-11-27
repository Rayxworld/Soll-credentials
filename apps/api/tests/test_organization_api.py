from datetime import datetime, timezone
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.dependencies import get_db
from app.main import app
from app.models import Organization, OrganizationMembership, User
from app.services.auth_session import create_auth_session


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app, client=("198.51.100.20", 50000)) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def create_authenticated_user(db_session, client):
    user = User(
        email=f"{uuid.uuid4().hex}@example.com",
        email_verified_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.flush()

    created = create_auth_session(db_session, user)
    db_session.commit()
    client.cookies.set("soll_session", created.session_token)
    client.cookies.set("soll_csrf", created.csrf_token)
    return user


def add_organization(db_session, user, *, name="SOLL Network", role="owner"):
    organization = Organization(
        name=name,
        slug=f"{uuid.uuid4().hex}",
        on_chain_org_id=None,
        stellar_owner_address=None,
        custody_mode="external",
    )
    db_session.add(organization)
    db_session.flush()

    membership = OrganizationMembership(
        organization_id=organization.id,
        user_id=user.id,
        role=role,
        is_active=True,
    )
    db_session.add(membership)
    db_session.flush()
    return organization, membership


def test_organization_list_requires_authentication(client):
    response = client.get("/api/v1/organizations")
    assert response.status_code == 401


def test_list_organizations_returns_only_active_user_memberships(
    client,
    db_session,
):
    user = create_authenticated_user(db_session, client)
    own_org, _ = add_organization(db_session, user)

    other_user = User(
        email=f"{uuid.uuid4().hex}@example.com",
        email_verified_at=datetime.now(timezone.utc),
    )
    db_session.add(other_user)
    db_session.flush()
    other_org, _ = add_organization(
        db_session,
        other_user,
        name="Another Tenant",
    )

    response = client.get("/api/v1/organizations")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(own_org.id)
    assert data[0]["name"] == "SOLL Network"
    assert data[0]["role"] == "owner"
    assert data[0]["chain_registered"] is False
    assert str(other_org.id) not in response.text


def test_organization_detail_requires_membership(client, db_session):
    user = create_authenticated_user(db_session, client)
    own_org, _ = add_organization(db_session, user)

    other_org = Organization(
        name="Private Tenant",
        slug=uuid.uuid4().hex,
    )
    db_session.add(other_org)
    db_session.flush()

    response = client.get(f"/api/v1/organizations/{other_org.id}")
    assert response.status_code == 404

    own_response = client.get(f"/api/v1/organizations/{own_org.id}")
    assert own_response.status_code == 200
    data = own_response.json()
    assert data["id"] == str(own_org.id)
    assert data["stellar_owner_address"] is None
    assert data["custody_mode"] == "external"


def test_inactive_membership_is_not_visible(client, db_session):
    user = create_authenticated_user(db_session, client)
    organization, membership = add_organization(db_session, user)
    membership.is_active = False
    db_session.flush()

    list_response = client.get("/api/v1/organizations")
    detail_response = client.get(f"/api/v1/organizations/{organization.id}")

    assert list_response.status_code == 200
    assert list_response.json() == []
    assert detail_response.status_code == 404



def test_create_organization_requires_authentication(client):
    response = client.post(
        "/api/v1/organizations",
        json={"name": "New Training Centre"},
    )
    assert response.status_code == 401


def test_create_organization_requires_csrf(client, db_session):
    create_authenticated_user(db_session, client)
    response = client.post(
        "/api/v1/organizations",
        json={"name": "New Training Centre"},
    )
    assert response.status_code == 403


def test_create_organization_assigns_creator_as_owner(client, db_session):
    user = create_authenticated_user(db_session, client)
    csrf_token = client.cookies.get("soll_csrf")

    response = client.post(
        "/api/v1/organizations",
        json={"name": "  Port Harcourt   Tech Academy  "},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Port Harcourt Tech Academy"
    assert data["role"] == "owner"
    assert data["is_active"] is True
    assert data["chain_registered"] is False
    assert data["slug"].startswith("port-harcourt-tech-academy-")

    membership = db_session.query(OrganizationMembership).filter_by(
        organization_id=uuid.UUID(data["id"]),
        user_id=user.id,
    ).one()
    assert membership.role == "owner"
    assert membership.is_active is True
