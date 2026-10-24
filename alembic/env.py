"""Konfigurasi Alembic.

URL database TIDAK ditulis di alembic.ini (jangan sampai kredensial masuk git).
Diambil dari app.core.config (env var DATABASE_URL), dan datanya hanya dibaca
saat menjalankan perintah alembic - bukan saat app FastAPI jalan.
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
if not settings.DATABASE_URL:
    raise SystemExit(
        "DATABASE_URL belum diisi di .env. Contoh:\n"
        "DATABASE_URL=postgresql+psycopg://postgres:<password-db>@db.<project-ref>.supabase.co:5432/postgres"
    )

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = None  # belum ada model SQLAlchemy; isi kalau mau autogenerate


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
