"""tabel audit_logs

Meniru migrations/legacy_sql/0002_audit_logs.sql.

Revision ID: 0002
Revises: 0001
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="audit_logs_pkey"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="audit_logs_created_by_fkey", ondelete="SET NULL"),
    )
    op.create_index("idx_audit_logs_created_by", "audit_logs", ["created_by"])
    op.create_index("idx_audit_logs_type", "audit_logs", ["type"])


def downgrade() -> None:
    op.drop_index("idx_audit_logs_type", table_name="audit_logs")
    op.drop_index("idx_audit_logs_created_by", table_name="audit_logs")
    op.drop_table("audit_logs")
