from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.dependencies import AuthContext, get_current_auth
from app.db.dependencies import get_db
from app.models import Organization, OrganizationMembership
from app.schemas.organization import OrganizationDetail, OrganizationSummary


router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _summary(
    organization: Organization,
    membership: OrganizationMembership,
) -> OrganizationSummary:
    return OrganizationSummary(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        role=membership.role,
        is_active=organization.is_active,
        chain_registered=organization.on_chain_org_id is not None,
        created_at=organization.created_at,
    )


@router.get("", response_model=list[OrganizationSummary])
def list_organizations(
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> list[OrganizationSummary]:
    """List only organizations the authenticated user actively belongs to."""
    rows = db.execute(
        select(Organization, OrganizationMembership)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Organization.id,
        )
        .where(
            OrganizationMembership.user_id == auth.user.id,
            OrganizationMembership.is_active.is_(True),
        )
        .order_by(Organization.name.asc(), Organization.id.asc())
    ).all()

    return [_summary(organization, membership) for organization, membership in rows]


@router.get(
    "/{organization_id}",
    response_model=OrganizationDetail,
)
def get_organization(
    organization_id: UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> OrganizationDetail:
    """Read an organization only when the caller has an active membership."""
    row = db.execute(
        select(Organization, OrganizationMembership)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Organization.id,
        )
        .where(
            Organization.id == organization_id,
            OrganizationMembership.user_id == auth.user.id,
            OrganizationMembership.is_active.is_(True),
        )
    ).first()

    # Use 404 for both missing organizations and non-members to avoid
    # disclosing whether another tenant exists.
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    organization, membership = row
    summary = _summary(organization, membership)

    return OrganizationDetail(
        **summary.model_dump(),
        stellar_owner_address=organization.stellar_owner_address,
        custody_mode=organization.custody_mode,
    )
