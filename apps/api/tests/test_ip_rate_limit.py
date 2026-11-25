import hashlib
import hmac
import ipaddress
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, Request
from sqlalchemy import select

from app.core.config import settings
from app.models import RateLimitBucket
from app.services.ip_rate_limit import (
    RateLimitPolicy,
    consume_rate_limit,
    hash_client_ip,
    resolve_client_ip,
)


def make_request(
    peer: str,
    forwarded: str | None = None,
) -> Request:
    headers = []

    if forwarded is not None:
        headers.append(
            (b"x-forwarded-for", forwarded.encode("ascii"))
        )

    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": headers,
            "client": (peer, 50000),
            "server": ("testserver", 80),
        }
    )


def test_direct_client_ip_ignores_untrusted_forwarded_header(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_cidrs", "")

    request = make_request(
        "198.51.100.10",
        "203.0.113.99",
    )

    assert resolve_client_ip(request) == ipaddress.ip_address(
        "198.51.100.10"
    )


def test_trusted_proxy_uses_first_untrusted_hop(monkeypatch):
    monkeypatch.setattr(
        settings,
        "trusted_proxy_cidrs",
        "10.0.0.0/8,192.0.2.0/24",
    )

    request = make_request(
        "10.0.0.5",
        "203.0.113.20, 192.0.2.10",
    )

    assert resolve_client_ip(request) == ipaddress.ip_address(
        "203.0.113.20"
    )


def test_trusted_proxy_rejects_malformed_forwarded_header(monkeypatch):
    monkeypatch.setattr(
        settings,
        "trusted_proxy_cidrs",
        "10.0.0.0/8",
    )

    request = make_request(
        "10.0.0.5",
        "not-an-ip",
    )

    with pytest.raises(HTTPException) as exc_info:
        resolve_client_ip(request)

    assert exc_info.value.status_code == 400


def test_ip_hash_is_keyed_and_does_not_contain_raw_address():
    address = ipaddress.ip_address("203.0.113.25")

    digest = hash_client_ip(address, "otp_request")

    assert len(digest) == 64
    assert digest != address.compressed
    assert address.compressed not in digest


def test_rate_limit_allows_requests_up_to_policy(
    db_session,
):
    address = ipaddress.ip_address("198.51.100.30")
    policy = RateLimitPolicy(limit=2, window_seconds=900)
    now = datetime(2026, 11, 25, 13, 0, tzinfo=timezone.utc)

    first = consume_rate_limit(
        db_session,
        "otp_verify",
        address,
        policy,
        now,
    )
    second = consume_rate_limit(
        db_session,
        "otp_verify",
        address,
        policy,
        now,
    )

    assert first.allowed is True
    assert first.request_count == 1
    assert second.allowed is True
    assert second.request_count == 2


def test_rate_limit_rejects_request_after_limit(
    db_session,
):
    address = ipaddress.ip_address("198.51.100.31")
    policy = RateLimitPolicy(limit=1, window_seconds=900)
    now = datetime(2026, 11, 25, 13, 0, tzinfo=timezone.utc)

    first = consume_rate_limit(
        db_session,
        "otp_verify",
        address,
        policy,
        now,
    )
    second = consume_rate_limit(
        db_session,
        "otp_verify",
        address,
        policy,
        now,
    )

    assert first.allowed is True
    assert second.allowed is False
    assert second.request_count == 2
    assert second.retry_after == 900


def test_rate_limit_counter_is_separate_per_scope(
    db_session,
):
    address = ipaddress.ip_address("198.51.100.32")
    policy = RateLimitPolicy(limit=1, window_seconds=900)
    now = datetime(2026, 11, 25, 13, 0, tzinfo=timezone.utc)

    request_decision = consume_rate_limit(
        db_session,
        "otp_request",
        address,
        policy,
        now,
    )
    verify_decision = consume_rate_limit(
        db_session,
        "otp_verify",
        address,
        policy,
        now,
    )

    assert request_decision.allowed is True
    assert verify_decision.allowed is True


def test_rate_limit_counter_resets_in_next_window(
    db_session,
):
    address = ipaddress.ip_address("198.51.100.33")
    policy = RateLimitPolicy(limit=1, window_seconds=900)
    now = datetime(2026, 11, 25, 13, 0, tzinfo=timezone.utc)

    first = consume_rate_limit(
        db_session,
        "otp_verify",
        address,
        policy,
        now,
    )
    next_window = consume_rate_limit(
        db_session,
        "otp_verify",
        address,
        policy,
        now + timedelta(minutes=15),
    )

    assert first.allowed is True
    assert next_window.allowed is True
    assert next_window.request_count == 1


def test_database_stores_hash_not_raw_ip(
    db_session,
):
    address = ipaddress.ip_address("198.51.100.34")
    policy = RateLimitPolicy(limit=5, window_seconds=900)
    now = datetime(2026, 11, 25, 13, 0, tzinfo=timezone.utc)

    consume_rate_limit(
        db_session,
        "otp_verify",
        address,
        policy,
        now,
    )

    bucket = db_session.scalar(
        select(RateLimitBucket).where(
            RateLimitBucket.scope == "otp_verify"
        )
    )

    assert bucket is not None
    assert bucket.ip_hash == hash_client_ip(address, "otp_verify")
    assert address.compressed not in bucket.ip_hash
