"""Base deklaratif SQLAlchemy.

Model di app/db/models/ HANYA mendeskripsikan skema (dipakai Alembic sebagai
`target_metadata`). Query aplikasi tetap SQL terparameter di repository.py
masing-masing fitur, sehingga mudah dibaca pemula.
"""
from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Nama constraint/index konsisten agar migrasi dapat diprediksi.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
