from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"

    __table_args__ = (

        CheckConstraint(
            "request_count >= 1",
            name="ck_rate_limit_buckets_request_count",
        ),
        CheckConstraint(
            "length(ip_hash) = 64",
            name="ck_rate_limit_buckets_ip_hash_length",
        ),
        Index(
            "ix_rate_limit_buckets_window_start",
            "window_start",
        ),
    )

    scope: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
    )

    ip_hash: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
    )

    request_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
