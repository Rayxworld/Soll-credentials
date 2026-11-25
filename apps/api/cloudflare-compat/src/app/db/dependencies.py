import asyncio
from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool


database_lock = asyncio.Lock()


async def get_db(request: Request) -> AsyncGenerator[Session, None]:
    env = request.scope["env"]
    hyperdrive = env.HYPERDRIVE

    database_url = URL.create(
        drivername="postgresql+pg8000",
        username=hyperdrive.user,
        password=hyperdrive.password,
        host=hyperdrive.host,
        port=int(hyperdrive.port),
        database=hyperdrive.database,
    )

    async with database_lock:
        engine = create_engine(
            database_url,
            poolclass=NullPool,
            connect_args={"ssl_context": False},
        )

        SessionLocal = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
            engine.dispose()
