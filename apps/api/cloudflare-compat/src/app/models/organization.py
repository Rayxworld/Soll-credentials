import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    LargeBinary,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    __table_args__ = (
        CheckConstraint(
            "on_chain_org_id IS NULL OR octet_length(on_chain_org_id) = 32",
            name="ck_organizations_on_chain_id_length",
        ),
        CheckConstraint(
            "custody_mode IS NULL OR custody_mode IN ('managed', 'external')",
            name="ck_organizations_custody_mode",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        nullable=False,
    )

    on_chain_org_id: Mapped[bytes | None] = mapped_column(
        LargeBinary(32),
        unique=True,
        nullable=True,
    )

    stellar_owner_address: Mapped[str | None] = mapped_column(
        String(56),
        nullable=True,
    )

    custody_mode: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
