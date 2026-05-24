"""Alembic env.py — configuração do ambiente de migrations."""
from __future__ import annotations
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Importa o metadata de todos os modelos para autogenerate
from app.db.base import Base
import app.models  # noqa — garante que todos os modelos sejam registrados

config = context.config

# Configuração de logging via alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Sobrescreve sqlalchemy.url com a variável de ambiente (SYNC — psycopg2)
sync_url = os.getenv("SYNC_DATABASE_URL") or os.getenv("DATABASE_URL", "").replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)
if sync_url:
    config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Gera SQL sem conexão ativa com o banco."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrations com conexão ativa."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
