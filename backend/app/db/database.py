"""
Configuração do banco de dados — SQLAlchemy 2.0 Async.

Engine assíncrono com asyncpg (runtime FastAPI) e utilitários de sessão.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Engine assíncrono ────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# ── Session factory ──────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Dependência FastAPI ──────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma AsyncSession por requisição; commit/rollback automático."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Health check ─────────────────────────────────────────────
async def ping_db() -> bool:
    """Retorna True se o banco está acessível."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Falha no ping ao banco: %s", exc)
        return False


# ── Criação de tabelas (apenas desenvolvimento) ───────────────
async def create_all_tables() -> None:
    """
    Cria todas as tabelas via Base.metadata.create_all.
    Em produção use: alembic upgrade head
    """
    from app.db.base import Base
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tabelas verificadas/criadas.")
