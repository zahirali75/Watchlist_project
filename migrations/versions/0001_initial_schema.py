"""skema dasar: users, movies, watchlists

Meniru migrations/legacy_sql/0001_initial_schema.sql apa adanya.
Database lama yang dibuat dari SQL itu: jalankan `alembic stamp 0002` (bukan upgrade).

Revision ID: 0001
Revises:
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import conv

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default=sa.text("'user'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id", name="users_pkey"),
        sa.UniqueConstraint("email", name="users_email_key"),
        sa.CheckConstraint("role IN ('user', 'admin')", name=conv("users_role_check")),
    )
    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("release_year", sa.Integer()),
        sa.Column("genre", sa.String(255)),
        sa.Column("director", sa.String(255)),
        sa.Column("overview", sa.Text()),
        sa.Column("poster_url", sa.Text()),
        sa.Column("rating", sa.Numeric(3, 1)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id", name="movies_pkey"),
    )
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), server_default=sa.text("'want_to_watch'")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id", name="watchlists_pkey"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="watchlists_user_id_fkey", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], name="watchlists_movie_id_fkey", ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "movie_id", name="watchlists_user_id_movie_id_key"),
        sa.CheckConstraint("status IN ('want_to_watch', 'watching', 'watched')", name=conv("watchlists_status_check")),
    )
    op.create_index("idx_watchlists_user_id", "watchlists", ["user_id"])
    op.create_index("idx_watchlists_movie_id", "watchlists", ["movie_id"])
    op.create_index("idx_movies_title", "movies", ["title"])


def downgrade() -> None:
    op.drop_index("idx_movies_title", table_name="movies")
    op.drop_index("idx_watchlists_movie_id", table_name="watchlists")
    op.drop_index("idx_watchlists_user_id", table_name="watchlists")
    op.drop_table("watchlists")
    op.drop_table("movies")
    op.drop_table("users")
