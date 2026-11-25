import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Organization, OrganizationMembership, User


ROLE_PERMISSIONS = {
    "owner": {
        "organization:read",
        "organization:update",
        "members:manage",
        "programs:manage",
        "recipients:manage",
        "templates:manage",
        "credentials:issue",
        "credentials:revoke",
        "credentials:read",
        "ownership:transfer",
    },
    "admin": {
        "organization:read",
        "organization:update",
        "members:manage",
        "programs:manage",
        "recipients:manage",
        "templates:manage",
        "credentials:issue",
        "credentials:revoke",
        "credentials:read",
    },
    "issuer": {
        "organization:read",
        "programs:read",
        "recipients:read",
        "templates:read",
        "credentials:issue",
        "credentials:read",
    },
}


def get_active_membership(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
) -> OrganizationMembership:
    membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.is_active.is_(True),
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have active access to this organization.",
        )

    user = db.get(User, user_id)
    organization = db.get(Organization, organization_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    if organization is None or not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive or unavailable.",
        )

    return membership


def require_permission(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    permission: str,
) -> OrganizationMembership:
    membership = get_active_membership(db, organization_id, user_id)

    permissions = ROLE_PERMISSIONS.get(membership.role, set())

    if permission not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )

    return membership
