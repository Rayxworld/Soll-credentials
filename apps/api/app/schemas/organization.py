import re
import unicodedata
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


OrganizationRole = Literal["owner", "admin", "issuer"]


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("Organization name must contain at least two characters.")
        return normalized


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
