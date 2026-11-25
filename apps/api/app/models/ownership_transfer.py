import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OwnershipTransfer(Base):
    __tablename__ = "ownership_transfers"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'cancelled', 'expired')",
            name="ck_ownership_transfers_status",
        ),
        CheckConstraint(
            "from_membership_id != to_membership_id",
            name="ck_ownership_transfers_different_memberships",
        ),
        CheckConstraint(
            "expires_at > initiated_at",
            name="ck_ownership_transfers_valid_expiration",
        ),
        CheckConstraint(
            "(accepted_by_user_id IS NULL AND accepted_at IS NULL) "
            "OR (accepted_by_user_id IS NOT NULL AND accepted_at IS NOT NULL)",
            name="ck_ownership_transfers_acceptance_pair",
        ),
        CheckConstraint(
            "completed_at IS NULL OR accepted_at IS NOT NULL",
            name="ck_ownership_transfers_completion_requires_acceptance",
        ),
        CheckConstraint(
            "status != 'completed' OR completed_at IS NOT NULL",
            name="ck_ownership_transfers_completed_timestamp",
        ),
        Index(
            "uq_ownership_transfers_one_pending_per_org",
            "organization_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    from_membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organization_memberships.id", ondelete="RESTRICT"),
        nullable=False,
    )

    to_membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organization_memberships.id", ondelete="RESTRICT"),
        nullable=False,
    )

    initiated_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    accepted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(16),
        default="pending",
        server_default="pending",
        nullable=False,
    )

    initiated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
