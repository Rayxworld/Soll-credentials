import hashlib
import hmac
import ipaddress
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network

from fastapi import HTTPException, Request, status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_otp_pepper
from app.models import RateLimitBucket


IPAddress = IPv4Address | IPv6Address
IPNetwork = IPv4Network | IPv6Network


@dataclass(frozen=True)
class RateLimitPolicy:
    limit: int
    window_seconds: int


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    request_count: int
    retry_after: int


RATE_LIMITS = {
    "otp_request": RateLimitPolicy(
        limit=20,
        window_seconds=60 * 60,
    ),
    "otp_verify": RateLimitPolicy(
        limit=30,
        window_seconds=15 * 60,
    ),
}


def _trusted_networks() -> list[IPNetwork]:
    networks: list[IPNetwork] = []

    for value in settings.trusted_proxy_cidrs.split(","):
        value = value.strip()

        if not value:
            continue

        try:
            networks.append(ipaddress.ip_network(value, strict=False))
        except ValueError as exc:
            raise RuntimeError(
                "TRUSTED_PROXY_CIDRS contains an invalid network."
            ) from exc

    return networks


def _is_trusted(
    address: IPAddress,
    networks: list[IPNetwork],
) -> bool:
    return any(
        address.version == network.version and address in network
        for network in networks
    )


def resolve_client_ip(request: Request) -> IPAddress:
    """
    Resolve the client address without trusting arbitrary forwarded headers.

    X-Forwarded-For is considered only when the immediate peer belongs to
    an explicitly configured trusted proxy network.
    """
    if request.client is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine client address.",
        )

    try:
        peer = ipaddress.ip_address(request.client.host)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client address.",
        ) from exc

    trusted_networks = _trusted_networks()

    if not _is_trusted(peer, trusted_networks):
        return peer

    forwarded = request.headers.get("x-forwarded-for")

    if not forwarded:
        return peer

    try:
        forwarded_addresses = [
            ipaddress.ip_address(value.strip())
            for value in forwarded.split(",")
        ]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid forwarded client address.",
        ) from exc

    if not forwarded_addresses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid forwarded client address.",
        )

    chain = forwarded_addresses + [peer]

    # Walk from the immediate peer toward the original client.
    # Trusted proxy hops are skipped; the first untrusted hop is the client.
    for address in reversed(chain):
        if not _is_trusted(address, trusted_networks):
            return address

    # The chain contained only trusted proxies.
    return forwarded_addresses[0]


def hash_client_ip(address: IPAddress, scope: str) -> str:
    """
    Produce a domain-separated HMAC digest.

    The database receives only this digest, never the raw IP address.
    """
    master_key = get_otp_pepper().encode("utf-8")

    derived_key = hmac.new(
        master_key,
        b"soll-credential:ip-rate-limit-key:v1",
        hashlib.sha256,
    ).digest()

    message = (
        f"soll-credential:ip-rate-limit:v1:{scope}:{address.compressed}"
    ).encode("utf-8")

    return hmac.new(
        derived_key,
        message,
        hashlib.sha256,
    ).hexdigest()


def consume_rate_limit(
    db: Session,
    scope: str,
    address: IPAddress,
    policy: RateLimitPolicy,
    now: datetime | None = None,
) -> RateLimitDecision:
    """
    Atomically increment one fixed-window counter using PostgreSQL upsert.

    The caller must commit the transaction even when the request is denied.
    """
    if policy.limit < 1 or policy.window_seconds < 1:
        raise ValueError("Rate-limit policy values must be positive.")

    current = now or datetime.now(timezone.utc)

    if current.tzinfo is None:
        raise ValueError("Rate-limit timestamps must be timezone-aware.")

    epoch = int(current.timestamp())
    window_epoch = (
        epoch // policy.window_seconds
    ) * policy.window_seconds

    window_start = datetime.fromtimestamp(
        window_epoch,
        tz=timezone.utc,
    )

    window_end_epoch = window_epoch + policy.window_seconds
    retry_after = max(
        1,
        math.ceil(window_end_epoch - current.timestamp()),
    )

    ip_hash = hash_client_ip(address, scope)

    statement = (
        insert(RateLimitBucket)
        .values(
            scope=scope,
            ip_hash=ip_hash,
            window_start=window_start,
            request_count=1,
            updated_at=current,
        )
        .on_conflict_do_update(
            index_elements=[
                RateLimitBucket.scope,
                RateLimitBucket.ip_hash,
                RateLimitBucket.window_start,
            ],
            set_={
                "request_count": RateLimitBucket.request_count + 1,
                "updated_at": current,
            },
        )
        .returning(RateLimitBucket.request_count)
    )

    request_count = db.scalar(statement)

    if request_count is None:
        raise RuntimeError("Rate-limit counter could not be updated.")

    return RateLimitDecision(
        allowed=request_count <= policy.limit,
        request_count=request_count,
        retry_after=retry_after,
    )


def enforce_ip_rate_limit(
    request: Request,
    db: Session,
    scope: str,
) -> None:
    policy = RATE_LIMITS[scope]
    address = resolve_client_ip(request)

    decision = consume_rate_limit(
        db=db,
        scope=scope,
        address=address,
        policy=policy,
    )

    # Persist the counter before OTP processing. This commit is required
    # even when the counter has exceeded its configured limit.
    db.commit()

    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={
                "Retry-After": str(decision.retry_after),
            },
        )
