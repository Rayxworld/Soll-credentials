import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models import OrganizationMembership, OwnershipTransfer, User
from app.services.ownership_transfer import (
    accept_ownership_transfer,
    cancel_ownership_transfer,
    expire_ownership_transfer,
    initiate_ownership_transfer,
)
from tests.test_models import make_base_records


def setup_transfer(db):
    records = make_base_records(db)
    owner, organization = records[0], records[1]

    target_user = User(email=f"{uuid.uuid4().hex}@example.com")
    db.add(target_user)
    db.flush()

    target = OrganizationMembership(
        organization_id=organization.id,
        user_id=target_user.id,
        role="issuer",
        is_active=True,
    )
    db.add(target)
    db.flush()

    return owner, organization, target_user, target


def test_initiate_transfer(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)

    transfer = initiate_ownership_transfer(
        db_session, organization.id, owner.id, target.id
    )

    assert transfer.status == "pending"
    assert transfer.initiated_by_user_id == owner.id
    assert transfer.to_membership_id == target.id
    assert transfer.expires_at > transfer.initiated_at


def test_non_owner_cannot_initiate_transfer(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)

    with pytest.raises(HTTPException) as error:
        initiate_ownership_transfer(
            db_session, organization.id, target_user.id, owner.id
        )

    assert error.value.status_code == 403


def test_inactive_target_cannot_receive_transfer(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)
    target.is_active = False

    with pytest.raises(HTTPException) as error:
        initiate_ownership_transfer(
            db_session, organization.id, owner.id, target.id
        )

    assert error.value.status_code == 400


def test_only_one_pending_transfer_per_organization(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)
    initiate_ownership_transfer(
        db_session, organization.id, owner.id, target.id
    )

    another_user = User(email=f"{uuid.uuid4().hex}@example.com")
    db_session.add(another_user)
    db_session.flush()

    another_target = OrganizationMembership(
        organization_id=organization.id,
        user_id=another_user.id,
        role="issuer",
    )
    db_session.add(another_target)
    db_session.flush()

    with pytest.raises(HTTPException) as error:
        initiate_ownership_transfer(
            db_session, organization.id, owner.id, another_target.id
        )

    assert error.value.status_code == 409


def test_incoming_member_accepts_and_becomes_owner(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)
    transfer = initiate_ownership_transfer(
        db_session, organization.id, owner.id, target.id
    )

    result = accept_ownership_transfer(
        db_session, transfer.id, target_user.id
    )

    assert result.status == "completed"
    assert result.accepted_by_user_id == target_user.id
    assert result.accepted_at is not None
    assert result.completed_at is not None
    assert owner_membership(db_session, organization.id).user_id == target_user.id
    assert db_session.get(OrganizationMembership, target.id).role == "owner"


def owner_membership(db, organization_id):
    return db.query(OrganizationMembership).filter_by(
        organization_id=organization_id,
        role="owner",
        is_active=True,
    ).one()


def test_wrong_user_cannot_accept_transfer(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)
    transfer = initiate_ownership_transfer(
        db_session, organization.id, owner.id, target.id
    )

    with pytest.raises(HTTPException) as error:
        accept_ownership_transfer(db_session, transfer.id, owner.id)

    assert error.value.status_code == 403
    assert db_session.get(OrganizationMembership, owner_membership(
        db_session, organization.id
    ).id).role == "owner"


def test_expired_transfer_cannot_be_accepted(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)
    transfer = initiate_ownership_transfer(
        db_session, organization.id, owner.id, target.id
    )
    now = datetime.now(timezone.utc)
    transfer.initiated_at = now - timedelta(days=1)
    transfer.expires_at = now - timedelta(seconds=1)
    db_session.flush()

    result = accept_ownership_transfer(
        db_session, transfer.id, target_user.id
    )

    assert result.status == "expired"
    assert owner_membership(db_session, organization.id).user_id == owner.id


def test_owner_can_cancel_pending_transfer(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)
    transfer = initiate_ownership_transfer(
        db_session, organization.id, owner.id, target.id
    )

    result = cancel_ownership_transfer(
        db_session, transfer.id, owner.id
    )

    assert result.status == "cancelled"
    assert owner_membership(db_session, organization.id).user_id == owner.id


def test_incoming_member_cannot_cancel_transfer(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)
    transfer = initiate_ownership_transfer(
        db_session, organization.id, owner.id, target.id
    )

    with pytest.raises(HTTPException) as error:
        cancel_ownership_transfer(db_session, transfer.id, target_user.id)

    assert error.value.status_code == 403


def test_expire_pending_transfer(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)
    transfer = initiate_ownership_transfer(
        db_session, organization.id, owner.id, target.id
    )
    now = datetime.now(timezone.utc)
    transfer.initiated_at = now - timedelta(days=1)
    transfer.expires_at = now - timedelta(seconds=1)
    db_session.flush()

    result = expire_ownership_transfer(db_session, transfer.id)

    assert result.status == "expired"


def test_completed_transfer_cannot_be_replayed(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)
    transfer = initiate_ownership_transfer(
        db_session, organization.id, owner.id, target.id
    )
    accept_ownership_transfer(db_session, transfer.id, target_user.id)

    with pytest.raises(HTTPException) as error:
        accept_ownership_transfer(db_session, transfer.id, target_user.id)

    assert error.value.status_code == 409


def test_invalid_expiration_is_rejected(db_session):
    owner, organization, target_user, target = setup_transfer(db_session)

    with pytest.raises(HTTPException) as error:
        initiate_ownership_transfer(
            db_session,
            organization.id,
            owner.id,
            target.id,
            expires_in=timedelta(days=8),
        )

    assert error.value.status_code == 400
