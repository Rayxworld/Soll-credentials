"""add database-backed IP rate limits

Revision ID: b3a7d91c4e62
Revises: ec7a8126cf01
Create Date: 2026-11-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3a7d91c4e62"
down_revision: Union[str, Sequence[str], None] = "ec7a8126cf01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rate_limit_buckets",
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("ip_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "window_start",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "request_count",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "request_count >= 1",
            name="ck_rate_limit_buckets_request_count",
        ),
        sa.CheckConstraint(
            "length(ip_hash) = 64",
            name="ck_rate_limit_buckets_ip_hash_length",
        ),
        sa.PrimaryKeyConstraint(
            "scope",
            "ip_hash",
            "window_start",
        ),

    )
    op.create_index(
        "ix_rate_limit_buckets_window_start",
        "rate_limit_buckets",
        ["window_start"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_rate_limit_buckets_window_start",
        table_name="rate_limit_buckets",
    )
    op.drop_table("rate_limit_buckets")
