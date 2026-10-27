"""tabel password_resets - token sekali pakai untuk lupa password

Alur: pengguna minta tautan reset -> token acak dibuat -> email dikirim ->
pengguna membuka tautan -> password diganti -> token ditandai terpakai.

Yang disimpan HANYA hash SHA-256 token (sama seperti refresh_tokens), dan token
kedaluwarsa dalam hitungan menit serta hanya bisa dipakai SEKALI.

Revision ID: 0006
Revises: 0005
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_resets",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_password_resets_user_id", "password_resets", ["user_id"])
    op.create_index("uq_password_resets_token_hash", "password_resets", ["token_hash"], unique=True)

    op.execute("ALTER TABLE password_resets ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon')
             AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            REVOKE ALL ON password_resets FROM anon, authenticated;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.drop_index("uq_password_resets_token_hash", table_name="password_resets")
    op.drop_index("idx_password_resets_user_id", table_name="password_resets")
    op.drop_table("password_resets")
