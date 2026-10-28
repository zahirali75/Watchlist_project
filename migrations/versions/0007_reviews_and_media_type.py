"""perubahan skema: media_type pada movies + tabel ulasan (reviews)

Dua hal yang belum ada di backend tetapi sudah dipakai frontend:

1. `movies.media_type` ('movie' | 'series') - frontend punya tab Movies dan
   Series serta label FILM/SERIES, tetapi kolomnya tidak ada, sehingga filter
   `?media_type=` diabaikan diam-diam dan label selalu salah. Baris lama diisi
   'movie' karena seluruh katalog lama memang film; setelah semua baris terisi
   barulah NOT NULL + CHECK dipasang. Nilai yang dipakai adalah 'series' (bukan
   'tv') agar konsisten dengan istilah yang dipakai aplikasi; frontend yang
   memakai 'tv' disesuaikan di sisi frontend, bukan di database.

2. Tabel `reviews` - fitur ulasan. Termasuk `is_hidden` untuk moderasi admin
   (ulasan disembunyikan tetap ada dan tetap terlihat oleh pemiliknya).
   RLS diaktifkan dan grant ke peran Data API Supabase (`anon`, `authenticated`)
   dicabut, sama seperti migrasi 0004/0006 - aplikasi tidak pernah memakai peran
   itu, jadi tidak ada yang berkurang fungsinya.

Semua langkah idempoten (IF NOT EXISTS + pemeriksaan pg_catalog) supaya aman
dijalankan pada database yang sebagian objeknya sudah ada.

Revision ID: 0007
Revises: 0006
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # ---- 1. movies.media_type -------------------------------------------------
    bind.execute(sa.text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS media_type VARCHAR(20)"))
    bind.execute(sa.text("UPDATE movies SET media_type = 'movie' WHERE media_type IS NULL"))
    bind.execute(sa.text("ALTER TABLE movies ALTER COLUMN media_type SET DEFAULT 'movie'"))
    bind.execute(sa.text("ALTER TABLE movies ALTER COLUMN media_type SET NOT NULL"))
    bind.execute(
        sa.text(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'movies_media_type_check') THEN
                ALTER TABLE movies ADD CONSTRAINT movies_media_type_check
                  CHECK (media_type IN ('movie', 'series'));
              END IF;
            END $$;
            """
        )
    )
    bind.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_movies_media_type ON movies (media_type)"))

    # ---- 2. tabel reviews ----------------------------------------------------
    bind.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
                rating NUMERIC(3, 1) NOT NULL,
                content TEXT NOT NULL,
                is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                updated_at TIMESTAMP NOT NULL DEFAULT now(),
                CONSTRAINT reviews_rating_range CHECK (rating >= 0 AND rating <= 10)
            )
            """
        )
    )
    bind.execute(
        sa.text("CREATE UNIQUE INDEX IF NOT EXISTS uq_reviews_user_id_movie_id ON reviews (user_id, movie_id)")
    )
    bind.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_reviews_movie_id ON reviews (movie_id)"))
    bind.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews (user_id)"))

    bind.execute(sa.text("ALTER TABLE reviews ENABLE ROW LEVEL SECURITY"))
    bind.execute(
        sa.text(
            """
            DO $$
            BEGIN
              IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon')
                 AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                REVOKE ALL ON reviews FROM anon, authenticated;
                REVOKE ALL ON SEQUENCE reviews_id_seq FROM anon, authenticated;
              END IF;
            END $$;
            """
        )
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS reviews")
    op.execute("DROP INDEX IF EXISTS idx_movies_media_type")
    op.execute("ALTER TABLE movies DROP CONSTRAINT IF EXISTS movies_media_type_check")
    op.execute("ALTER TABLE movies DROP COLUMN IF EXISTS media_type")
