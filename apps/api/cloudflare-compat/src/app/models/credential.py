import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Credential(Base):
    __tablename__ = "credentials"

    __table_args__ = (
        CheckConstraint(
            "octet_length(credential_id) = 32",
            name="ck_credentials_id_length",
        ),
        CheckConstraint(
            "octet_length(commitment) = 32",
            name="ck_credentials_commitment_length",
        ),
        CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= issued_at",
            name="ck_credentials_revocation_after_issuance",
        ),
        CheckConstraint(
            "revoked_at IS NOT NULL OR revocation_reason IS NULL",
            name="ck_credentials_reason_requires_revocation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    credential_id: Mapped[bytes] = mapped_column(
        LargeBinary(32), unique=True, nullable=False,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recipients.id", ondelete="RESTRICT"),
        nullable=False,
    )

    program_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("programs.id", ondelete="RESTRICT"),
        nullable=True,
    )

    template_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("certificate_template_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )

    issued_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    commitment: Mapped[bytes] = mapped_column(
        LargeBinary(32), nullable=False,
    )

    credential_data: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False,
    )

    blinding_value_encrypted: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False,
    )

    pdf_storage_key: Mapped[str] = mapped_column(
        String(500), nullable=False,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    revocation_reason: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
    )
