"""tabel refresh_tokens - perpanjangan sesi tanpa login ulang

Latar belakang: JWT sebelumnya hanya berlaku 60 menit tanpa jalur perpanjangan,
sehingga pengguna terlempar ke halaman login di tengah pemakaian.

Yang disimpan HANYA hash SHA-256 dari token, bukan tokennya sendiri. Bila isi
tabel ini bocor, token tetap tidak bisa dipakai untuk login.

Sesi yang sudah dipakai dirotasi (ditolak) supaya token lama tidak bisa dipakai
ulang. `revoked_at` menandai sesi yang dicabut (logout / ganti password).

RLS diaktifkan dan hak akses peran Supabase (`anon`, `authenticated`) dicabut,
konsisten dengan migrasi 0004.

Revision ID: 0005
Revises: 0004
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("uq_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    # Perlindungan yang sama seperti tabel lain (lihat migrasi 0004).
    op.execute("ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon')
             AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            REVOKE ALL ON refresh_tokens FROM anon, authenticated;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.drop_index("uq_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
