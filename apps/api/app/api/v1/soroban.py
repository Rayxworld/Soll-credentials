from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.dependencies import AuthContext, get_current_auth
from app.core.config import settings
from app.db.dependencies import get_db
from app.models import Organization, OrganizationMembership
from app.schemas.soroban import (
    IssuerAuthorizationStatus,
    PublicCredentialStatus,
)
from app.services.ip_rate_limit import enforce_ip_rate_limit
from app.services.soroban import (
    SorobanNotConfiguredError,
    SorobanUnavailableError,
    get_credential_record,
    is_issuer_authorized,
)

router = APIRouter(tags=["Soroban"])


def _raise_chain_error(exc: Exception) -> None:
    if isinstance(exc, SorobanNotConfiguredError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="On-chain verification is not configured.",
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="The Stellar network could not be queried.",
    ) from exc


@router.get(
    "/public/credentials/{credential_id}",
    response_model=PublicCredentialStatus,
)
def get_public_credential_status(
    request: Request,
    credential_id: str = Path(pattern=r"^[0-9a-fA-F]{64}$"),
    db: Session = Depends(get_db),
) -> PublicCredentialStatus:
    """Return rate-limited public on-chain status; no recipient data is exposed."""
    enforce_ip_rate_limit(request, db, "public_credential")

    try:
        record = get_credential_record(bytes.fromhex(credential_id))
    except (SorobanNotConfiguredError, SorobanUnavailableError) as exc:
        _raise_chain_error(exc)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found.",
        )

    return PublicCredentialStatus(
        credential_id=credential_id.lower(),
        organization_id=record["organization_id"].hex(),
        commitment=record["commitment"].hex(),
        issuer=record["issuer"],
        issued_at=record["issued_at"],
        revoked=record["revoked"],
        network=settings.stellar_network,
    )


@router.get(
    "/organizations/{organization_id}/issuers/{issuer_address}/authorization",
    response_model=IssuerAuthorizationStatus,
)
def get_issuer_authorization_status(
    organization_id: UUID,
    issuer_address: str = Path(pattern=r"^G[A-Z2-7]{55}$"),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> IssuerAuthorizationStatus:
    """Check on-chain issuer status for an organisation the caller belongs to."""
    organization = db.scalar(
        select(Organization)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Organization.id,
        )
        .where(
            Organization.id == organization_id,
            OrganizationMembership.user_id == auth.user.id,
            OrganizationMembership.is_active.is_(True),
        )
    )
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    if not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization is inactive.",
        )
    if organization.on_chain_org_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization is not registered on-chain.",
        )

    try:
        authorized = is_issuer_authorized(
            organization.on_chain_org_id,
            issuer_address,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Stellar issuer address.",
        ) from exc
    except (SorobanNotConfiguredError, SorobanUnavailableError) as exc:
        _raise_chain_error(exc)

    return IssuerAuthorizationStatus(
        organization_id=organization.id,
        issuer_address=issuer_address,
        authorized=authorized,
    )
