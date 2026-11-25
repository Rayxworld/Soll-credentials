import hmac

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.db.dependencies import get_db
from app.core.config import settings, set_otp_pepper, reset_otp_pepper


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)


@app.middleware("http")
async def inject_worker_secrets(request: Request, call_next):
    env = request.scope.get("env")
    pepper = getattr(env, "OTP_PEPPER", None) if env else None

    if not pepper:
        return JSONResponse(
            status_code=503,
            content={"detail": "Required Worker secret is not configured."},
        )

    token = set_otp_pepper(pepper)
    try:
        return await call_next(request)
    finally:
        reset_otp_pepper(token)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "running",
    }


async def require_compat_token(
    request: Request,
    authorization: str | None = Header(default=None),
) -> None:
    env = request.scope["env"]
    expected_token = getattr(env, "COMPAT_TEST_TOKEN", None)

    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Diagnostic authentication is not configured.",
        )

    if not authorization or not hmac.compare_digest(
        authorization,
        f"Bearer {expected_token}",
    ):
        raise HTTPException(status_code=401, detail="Unauthorized.")


async def get_compat_db(
    request: Request,
    _: None = Depends(require_compat_token),
):
    async for db in get_db(request):
        yield db


@app.get("/compat/database")
async def compatibility_database_test(
    db: Session = Depends(get_compat_db),
):
    try:
        result = db.execute(text("""
            SELECT
                1 AS test_result,
                current_database() AS database_name,
                current_user AS database_user,
                current_setting('server_version') AS server_version
        """)).mappings().one()

        return {
            "status": "success",
            "connection": "established",
            "provider": "Neon PostgreSQL via Cloudflare Hyperdrive",
            "result": dict(result),
        }
    except Exception as exc:
        print(f"Hyperdrive diagnostic failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Database diagnostic failed.",
        ) from exc
