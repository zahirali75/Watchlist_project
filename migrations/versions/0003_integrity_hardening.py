"""penguatan integritas data (PERUBAHAN SKEMA BARU, bisa ditinjau terpisah)

- users.role dan watchlists.status menjadi NOT NULL (NULL lama diisi default dulu).
- CHECK movies.rating 0..10 dan movies.release_year 1888..2100 (NOT VALID: hanya
  baris baru/ubah yang diperiksa; data lama tidak menggagalkan migrasi).
  Setelah data lama dibersihkan: ALTER TABLE movies VALIDATE CONSTRAINT <nama>;
- UNIQUE INDEX lower(email): email tidak boleh kembar walau beda huruf besar/kecil.
  Migrasi berhenti dengan pesan jelas bila sudah ada email kembar.

Tidak diubah (disengaja): tipe TIMESTAMP -> TIMESTAMPTZ pada users/movies/watchlists,
karena konversi data lama perlu keputusan zona waktu. Lihat docs/database.md.

Revision ID: 0003
Revises: 0002
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    duplicates = bind.execute(
        sa.text("SELECT lower(email) AS e, COUNT(*) AS n FROM users GROUP BY lower(email) HAVING COUNT(*) > 1")
    ).fetchall()
    if duplicates:
        raise RuntimeError(
            "Migrasi 0003 dihentikan: ada email kembar (beda huruf besar/kecil): "
            + ", ".join(row.e for row in duplicates)
            + ". Rapikan datanya lalu jalankan ulang."
        )

    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")
    op.execute("UPDATE watchlists SET status = 'want_to_watch' WHERE status IS NULL")
    op.alter_column("users", "role", existing_type=sa.String(50), nullable=False)
    op.alter_column("watchlists", "status", existing_type=sa.String(50), nullable=False)

    op.execute(
        "ALTER TABLE movies ADD CONSTRAINT movies_rating_range "
        "CHECK (rating IS NULL OR (rating >= 0 AND rating <= 10)) NOT VALID"
    )
    op.execute(
        "ALTER TABLE movies ADD CONSTRAINT movies_release_year_range "
        "CHECK (release_year IS NULL OR (release_year >= 1888 AND release_year <= 2100)) NOT VALID"
    )
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_email_lower", table_name="users")
    op.execute("ALTER TABLE movies DROP CONSTRAINT IF EXISTS movies_release_year_range")
    op.execute("ALTER TABLE movies DROP CONSTRAINT IF EXISTS movies_rating_range")
    op.alter_column("watchlists", "status", existing_type=sa.String(50), nullable=True)
    op.alter_column("users", "role", existing_type=sa.String(50), nullable=True)
