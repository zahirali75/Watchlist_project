# CineList: backend historis vs backend aktif

| Area | Historis (`backend/`) | Aktif (`app/`) |
|---|---|---|
| Entry point | Sekarang alias kompatibilitas ke `app.main` | `app/main.py` (entry point kanonis, dipakai `run.sh`) |
| Akses database | Sekarang mengekspor `get_engine`/`get_connection` yang sama | PostgreSQL langsung melalui SQLAlchemy Core + psycopg |
| Secret JWT | Tidak ada konfigurasi terpisah; memakai config aplikasi aktif | Wajib disediakan lewat `SECRET_KEY`; tidak ada fallback |
| ID user | Mengikuti implementasi aktif berbasis UUID | UUID, sesuai DDL aktif |
| Struktur | Alias ke struktur aktif | Router, schemas, services, repositories, core |
| Otorisasi | Menggunakan dependency & router aktif yang sama | Endpoint user dan audit-log admin-only; ownership watchlist diperiksa |
| Error | Menggunakan handler aplikasi aktif | Handler error terpusat dengan pesan umum untuk error tak terduga |

## Status migrasi query

Semua repository aktif, kedua seeder, serta compatibility path `backend/` kini menggunakan PostgreSQL langsung melalui SQLAlchemy Core dan `DATABASE_URL`. Pemindaian source executable tidak menemukan `create_client`, `supabase.table`, `get_supabase`, atau `.table(...).execute()`.

Kode lama Supabase pada `backend/main.py` dan `backend/database.py` telah diganti dengan compatibility shim; query Supabase tidak lagi ada di source executable saat ini. Riwayat Git masih mempertahankan versi sebelumnya untuk audit/perbandingan.

## Batasan yang masih harus dituntaskan

- `alembic/versions/` belum memiliki revision aktif dan `target_metadata` masih `None`; DDL saat ini memakai file SQL manual.
- Database testing/production tidak disertakan dan driver `psycopg` tidak terpasang di lingkungan audit, jadi koneksi PostgreSQL dan query langsung belum diuji runtime.
- Implementasi role pada JWT masih berupa claim token; perubahan role tidak segera membatalkan token yang sudah diterbitkan.
- Audit log belum mencatat semua aktivitas (misalnya login gagal dan perubahan watchlist), dan kegagalan pencatatan audit saat ini tidak menggagalkan operasi utama.
