"""Isolated runtime compatibility probe for SOLL Credential dependencies."""

from importlib.metadata import version
import platform

from fastapi import FastAPI
from sqlalchemy import create_engine
from workers import asgi

app = FastAPI(title="SOLL Credential Cloudflare Compatibility Probe")


@app.get("/")
async def root():
    return {"service": "soll-credential-cloudflare-compat", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/compat")
async def compatibility():
    # Constructing the engine loads SQLAlchemy's PostgreSQL dialect and pg8000
    # driver without opening a database connection.
    engine = create_engine(
        "postgresql+pg8000://compat:compat@127.0.0.1:5432/compat",
        pool_pre_ping=False,
    )
    try:
        dialect_name = engine.dialect.name
        driver_name = engine.dialect.driver
    finally:
        engine.dispose()

    # Importing pg8000 explicitly verifies that the driver is importable
    # inside the Python Worker runtime.
    import pg8000

    return {
        "python": platform.python_version(),
        "fastapi": version("fastapi"),
        "sqlalchemy": version("SQLAlchemy"),
        "pg8000": version("pg8000"),
        "pg8000_module": pg8000.__name__,
        "sqlalchemy_dialect": dialect_name,
        "sqlalchemy_driver": driver_name,
    }


Default = asgi.entrypoint(app)
