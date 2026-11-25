import uuid

import pytest
from fastapi import HTTPException

from app.models import Organization, OrganizationMembership, User
from app.services.authorization import (
    get_active_membership,
    require_permission,
)


def create_member(db, role="owner", active=True):
    user = User(email=f"{uuid.uuid4().hex}@example.com")
    organization = Organization(
        name="Test Organization",
        slug=uuid.uuid4().hex,
    )
    db.add_all([user, organization])
    db.flush()

    membership = OrganizationMembership(
        organization_id=organization.id,
        user_id=user.id,
        role=role,
        is_active=active,
    )
    db.add(membership)
    db.flush()

    return user, organization, membership


@pytest.mark.parametrize(
    "role,permission,allowed",
    [
        ("owner", "ownership:transfer", True),
        ("owner", "credentials:revoke", True),
        ("admin", "ownership:transfer", False),
        ("admin", "members:manage", True),
        ("issuer", "credentials:issue", True),
        ("issuer", "credentials:revoke", False),
        ("issuer", "templates:manage", False),
    ],
)
def test_role_permissions(db_session, role, permission, allowed):
    user, organization, _ = create_member(db_session, role)

    if allowed:
        membership = require_permission(
            db_session, organization.id, user.id, permission
        )
        assert membership.role == role
    else:
        with pytest.raises(HTTPException) as error:
            require_permission(
                db_session, organization.id, user.id, permission
            )

        assert error.value.status_code == 403


def test_cross_organization_access_is_denied(db_session):
    user, organization, _ = create_member(db_session)
    another_organization = Organization(
        name="Another Organization",
        slug=uuid.uuid4().hex,
    )
    db_session.add(another_organization)
    db_session.flush()

    with pytest.raises(HTTPException) as error:
        get_active_membership(
            db_session, another_organization.id, user.id
        )

    assert error.value.status_code == 403


def test_inactive_membership_is_denied(db_session):
    user, organization, _ = create_member(
        db_session, active=False
    )

    with pytest.raises(HTTPException) as error:
        get_active_membership(
            db_session, organization.id, user.id
        )

    assert error.value.status_code == 403


def test_inactive_user_is_denied(db_session):
    user, organization, _ = create_member(db_session)
    user.is_active = False
    db_session.flush()

    with pytest.raises(HTTPException) as error:
        get_active_membership(
            db_session, organization.id, user.id
        )

    assert error.value.status_code == 403


def test_inactive_organization_is_denied(db_session):
    user, organization, _ = create_member(db_session)
    organization.is_active = False
    db_session.flush()

    with pytest.raises(HTTPException) as error:
        get_active_membership(
            db_session, organization.id, user.id
        )

    assert error.value.status_code == 403
