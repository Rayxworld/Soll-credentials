from datetime import datetime, timedelta, timezone
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Organization,
    OrganizationMembership,
    OwnershipTransfer,
    User,
)


def _error(code: int, message: str) -> HTTPException:
    return HTTPException(status_code=code, detail=message)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lock_organization(db: Session, organization_id: uuid.UUID):
    organization = db.scalar(
        select(Organization)
        .where(Organization.id == organization_id)
        .with_for_update()
    )
    if organization is None or not organization.is_active:
        raise _error(404, "Organization not found or inactive.")
    return organization


def _transfer_organization_id(
    db: Session,
    transfer_id: uuid.UUID,
) -> uuid.UUID:
    organization_id = db.scalar(
        select(OwnershipTransfer.organization_id).where(
            OwnershipTransfer.id == transfer_id
        )
    )
    if organization_id is None:
        raise _error(404, "Ownership transfer not found.")
    return organization_id


def _lock_transfer(
    db: Session,
    transfer_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> OwnershipTransfer:
    transfer = db.scalar(
        select(OwnershipTransfer)
        .where(
            OwnershipTransfer.id == transfer_id,
            OwnershipTransfer.organization_id == organization_id,
        )
        .with_for_update()
    )
    if transfer is None:
        raise _error(404, "Ownership transfer not found.")
    return transfer


def initiate_ownership_transfer(
    db: Session,
    organization_id: uuid.UUID,
    initiated_by_user_id: uuid.UUID,
    target_membership_id: uuid.UUID,
    expires_in: timedelta = timedelta(hours=24),
) -> OwnershipTransfer:
    if expires_in <= timedelta(0) or expires_in > timedelta(days=7):
        raise _error(400, "Transfer expiration must be between 0 and 7 days.")

    _lock_organization(db, organization_id)
    db.flush()

    current_owner = db.scalar(
        select(OrganizationMembership)
        .where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == initiated_by_user_id,
            OrganizationMembership.role == "owner",
            OrganizationMembership.is_active.is_(True),
        )
        .with_for_update()
    )
    if current_owner is None:
        raise _error(403, "Only the active organization owner can initiate a transfer.")

    initiating_user = db.get(User, initiated_by_user_id)
    if initiating_user is None or not initiating_user.is_active:
        raise _error(403, "The initiating user is inactive.")

    target = db.scalar(
        select(OrganizationMembership)
        .where(
            OrganizationMembership.id == target_membership_id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.is_active.is_(True),
        )
        .with_for_update()
    )
    if target is None or target.id == current_owner.id:
        raise _error(400, "Target must be another active organization member.")

    if target.role not in {"admin", "issuer"}:
        raise _error(400, "Target must be an active admin or issuer.")

    target_user = db.get(User, target.user_id)
    if target_user is None or not target_user.is_active:
        raise _error(400, "Target user is inactive.")

    pending = db.scalar(
        select(OwnershipTransfer)
        .where(
            OwnershipTransfer.organization_id == organization_id,
            OwnershipTransfer.status == "pending",
        )
        .with_for_update()
    )

    now = _now()
    if pending is not None:
        if pending.expires_at <= now:
            pending.status = "expired"
            db.flush()
        else:
            raise _error(409, "An ownership transfer is already pending.")

    transfer = OwnershipTransfer(
        organization_id=organization_id,
        from_membership_id=current_owner.id,
        to_membership_id=target.id,
        initiated_by_user_id=initiated_by_user_id,
        status="pending",
        initiated_at=now,
        expires_at=now + expires_in,
    )
    db.add(transfer)
    db.flush()
    return transfer


def accept_ownership_transfer(
    db: Session,
    transfer_id: uuid.UUID,
    accepting_user_id: uuid.UUID,
) -> OwnershipTransfer:
    # Consistent lock order: organization, transfer, then memberships.
    organization_id = _transfer_organization_id(db, transfer_id)
    _lock_organization(db, organization_id)
    db.flush()
    transfer = _lock_transfer(db, transfer_id, organization_id)

    if transfer.status != "pending":
        raise _error(409, "This ownership transfer is no longer pending.")

    now = _now()
    if transfer.expires_at <= now:
        transfer.status = "expired"
        db.flush()
        return transfer

    memberships = db.scalars(
        select(OrganizationMembership)
        .where(
            OrganizationMembership.id.in_(
                [transfer.from_membership_id, transfer.to_membership_id]
            )
        )
        .order_by(OrganizationMembership.id)
        .with_for_update()
    ).all()

    membership_map = {membership.id: membership for membership in memberships}
    old_owner = membership_map.get(transfer.from_membership_id)
    new_owner = membership_map.get(transfer.to_membership_id)

    if old_owner is None or new_owner is None:
        raise _error(409, "Transfer memberships are unavailable.")

    if (
        old_owner.organization_id != organization_id
        or new_owner.organization_id != organization_id
        or not old_owner.is_active
        or old_owner.role != "owner"
        or old_owner.user_id != transfer.initiated_by_user_id
    ):
        raise _error(409, "The original ownership is no longer valid.")

    if not new_owner.is_active or new_owner.user_id != accepting_user_id:
        raise _error(403, "Only the designated active member can accept this transfer.")

    accepting_user = db.get(User, accepting_user_id)
    if accepting_user is None or not accepting_user.is_active:
        raise _error(403, "The accepting user is inactive.")

    old_owner.role = "admin"
    db.flush()

    new_owner.role = "owner"
    transfer.accepted_by_user_id = accepting_user_id
    transfer.accepted_at = now
    transfer.completed_at = now
    transfer.status = "completed"

    db.flush()
    return transfer


def cancel_ownership_transfer(
    db: Session,
    transfer_id: uuid.UUID,
    cancelling_user_id: uuid.UUID,
) -> OwnershipTransfer:
    organization_id = _transfer_organization_id(db, transfer_id)
    _lock_organization(db, organization_id)
    db.flush()
    transfer = _lock_transfer(db, transfer_id, organization_id)

    if transfer.status != "pending":
        raise _error(409, "This ownership transfer is no longer pending.")

    owner = db.scalar(
        select(OrganizationMembership)
        .where(OrganizationMembership.id == transfer.from_membership_id)
        .with_for_update()
    )

    if (
        owner is None
        or not owner.is_active
        or owner.role != "owner"
        or owner.user_id != cancelling_user_id
        or transfer.initiated_by_user_id != cancelling_user_id
    ):
        raise _error(403, "Only the initiating active owner can cancel this transfer.")

    if transfer.expires_at <= _now():
        transfer.status = "expired"
    else:
        transfer.status = "cancelled"

    db.flush()
    return transfer


def expire_ownership_transfer(
    db: Session,
    transfer_id: uuid.UUID,
) -> OwnershipTransfer:
    organization_id = _transfer_organization_id(db, transfer_id)
    _lock_organization(db, organization_id)
    db.flush()
    transfer = _lock_transfer(db, transfer_id, organization_id)

    if (
        transfer.status == "pending"
        and transfer.expires_at <= _now()
    ):
        transfer.status = "expired"
        db.flush()

    return transfer
