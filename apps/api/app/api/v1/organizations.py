import re
import unicodedata
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.dependencies import AuthContext, get_current_auth, require_csrf
from app.db.dependencies import get_db
from app.models import Organization, OrganizationMembership
from app.schemas.organization import (
    OrganizationCreateRequest,
    OrganizationDetail,
    OrganizationSummary,
)


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


def _make_slug(name: str) -> str:
    """Create a URL-safe, non-empty slug without trusting client input."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    base = (base or "organization")[:68].rstrip("-")
    return f"{base}-{uuid4().hex[:8]}"


@router.post(
    "",
    response_model=OrganizationSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    payload: OrganizationCreateRequest,
    auth: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> OrganizationSummary:
    """Create an organization and make the authenticated creator its owner."""
    organization = Organization(
        name=payload.name,
        slug=_make_slug(payload.name),
    )
    try:
        db.add(organization)
        db.flush()

        membership = OrganizationMembership(
            organization_id=organization.id,
            user_id=auth.user.id,
            role="owner",
            is_active=True,
        )
        db.add(membership)
        db.flush()
        db.refresh(organization)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The organization could not be created because of a data conflict.",
        ) from exc
    except Exception:
        db.rollback()
        raise

    return _summary(organization, membership)


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
