# Migrasi skema PostgreSQL

Aplikasi aktif terhubung ke PostgreSQL secara langsung melalui `DATABASE_URL`. Query API menggunakan SQLAlchemy Core dan driver `psycopg`, bukan Supabase SDK/PostgREST.

## Pembuatan database baru

Jalankan salah satu file untuk skema dasar, lalu migrasi audit log:

```bash
psql "postgresql://user:password@localhost:5432/cinelist" -f schema.sql
psql "postgresql://user:password@localhost:5432/cinelist" -f migrations/legacy_sql/0002_audit_logs.sql
```

`schema.sql` dan `0001_initial_schema.sql` adalah dua representasi skema awal yang sepadan; jangan menjalankan keduanya untuk membuat skema yang sama. `0002_audit_logs.sql` diperlukan oleh layanan audit log.

## Database yang sudah ada

Backup dahulu dan periksa tabel/constraint yang benar-benar tersedia. `CREATE TABLE IF NOT EXISTS` tidak memperbaiki tabel existing apabila kolom atau tipe datanya berbeda. Jangan menjalankan DDL terhadap database produksi tanpa rencana rollback.

## Alembic

Sumber migrasi aktif adalah Alembic: `migrations/versions/` (revision `0001`, `0002`, `0003`). Konfigurasi ada di `alembic.ini` dan `migrations/env.py`, serta membaca `DATABASE_URL` dari environment/.env. Folder `alembic/` di root sudah tidak dipakai.

Folder `legacy_sql/` ini hanya arsip. Untuk database yang dibuat dari file SQL di atas, pastikan kedua file (termasuk `audit_logs`) sudah dijalankan, lalu `alembic stamp 0002`, tinjau revision `0003` dan `0004`, baru `alembic upgrade head`. `stamp` tidak membuat tabel apa pun — bila `audit_logs` belum ada saat stamp dijalankan, tabel itu tidak akan pernah terbuat. Lihat `docs/database.md`.
