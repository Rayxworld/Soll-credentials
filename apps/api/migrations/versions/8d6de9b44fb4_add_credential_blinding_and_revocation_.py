"""add credential blinding and revocation constraints

Revision ID: 8d6de9b44fb4
Revises: f2b921498e74
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8d6de9b44fb4"
down_revision: Union[str, Sequence[str], None] = "f2b921498e74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "credentials",
        sa.Column("blinding_value_encrypted", sa.LargeBinary(), nullable=False),
    )
    op.create_check_constraint(
        "ck_credentials_revocation_after_issuance",
        "credentials",
        "revoked_at IS NULL OR revoked_at >= issued_at",
    )
    op.create_check_constraint(
        "ck_credentials_reason_requires_revocation",
        "credentials",
        "revoked_at IS NOT NULL OR revocation_reason IS NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_credentials_reason_requires_revocation",
        "credentials",
        type_="check",
    )
    op.drop_constraint(
        "ck_credentials_revocation_after_issuance",
        "credentials",
        type_="check",
    )
    op.drop_column("credentials", "blinding_value_encrypted")
