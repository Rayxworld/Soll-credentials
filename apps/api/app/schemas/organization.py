from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


OrganizationRole = Literal["owner", "admin", "issuer"]


class OrganizationSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    role: OrganizationRole
    is_active: bool
    chain_registered: bool
    created_at: datetime


class OrganizationDetail(OrganizationSummary):
    stellar_owner_address: str | None
    custody_mode: Literal["managed", "external"] | None
