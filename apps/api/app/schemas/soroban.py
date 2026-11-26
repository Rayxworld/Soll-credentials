from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PublicCredentialStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    credential_id: str
    organization_id: str
    commitment: str
    issuer: str
    issued_at: int
    revoked: bool
    network: str


class IssuerAuthorizationStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID
    issuer_address: str
    authorized: bool
