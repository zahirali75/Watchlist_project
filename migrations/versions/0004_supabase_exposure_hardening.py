"""pengamanan paparan tabel untuk PostgreSQL Supabase (Data API)

Latar belakang: di Supabase, tabel di schema `public` dapat dijangkau lewat Data
API oleh peran `anon` dan `authenticated` bila grant-nya ada. Tabel `users` memuat
`password_hash`, sehingga paparan itu tidak boleh terjadi.

Yang dilakukan (semua idempoten dan aman bila peran Supabase tidak ada):
1. Pemeriksaan awal: peran yang menjalankan migrasi harus pemilik tabel atau
   memiliki BYPASSRLS. Bila tidak, RLS tanpa policy akan memblokir aplikasi sendiri,
   jadi migrasi berhenti dengan pesan jelas.
2. ENABLE ROW LEVEL SECURITY pada keempat tabel (defense in depth; tanpa policy,
   peran non-pemilik tidak melihat baris apa pun).
3. Bila peran `anon`/`authenticated` ada: cabut semua hak akses tabel dan sequence
   di schema public, dan cabut default privilege agar tabel baru tidak terbuka otomatis.

Downgrade hanya mematikan RLS. Grant TIDAK dikembalikan: membuka kembali akses ke
Data API tidak boleh terjadi lewat downgrade secara diam-diam.

Revision ID: 0004
Revises: 0003
"""
from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

TABLES = ("users", "movies", "watchlists", "audit_logs")


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE r record;
        BEGIN
          IF NOT (SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user) THEN
            FOR r IN
              SELECT c.relname, pg_get_userbyid(c.relowner) AS owner
              FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
              WHERE n.nspname = 'public' AND c.relkind = 'r'
                AND c.relname IN ('users', 'movies', 'watchlists', 'audit_logs')
            LOOP
              IF r.owner <> current_user THEN
                RAISE EXCEPTION 'Migrasi 0004 dihentikan: role % bukan pemilik tabel % dan tidak memiliki BYPASSRLS. Aktifkan RLS dengan role pemilik atau berikan BYPASSRLS ke role aplikasi.', current_user, r.relname;
              END IF;
            END LOOP;
          END IF;
        END $$;
        """
    )
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon')
             AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
            REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
