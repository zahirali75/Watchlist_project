# Audit arsip Watchlist Project

Laporan ini mencakup dua tahap:

1. Penataan arsip sebelumnya: dokumentasi, template environment dan penjelasan duplikasi diperbaiki tanpa mengganti sumber original.
2. Audit backend lanjutan: repository aktif `app/` dan kedua seeder telah diarahkan ke PostgreSQL langsung, error database tidak lagi mengekspos `dbMessage`, parameter hashing password diperkuat, serta dokumentasi ERD dan setup diperbarui.

## Batas dan preservasi

- Sumber arsip asli tetap terpisah dan tidak ditimpa.
- Folder `.git/` dipertahankan sehingga riwayat historis tetap tersedia. `backend/main.py` dan `backend/database.py` saat ini adalah compatibility shim tanpa query Supabase; keduanya meneruskan ke koneksi/aplikasi PostgreSQL aktif.
- `run.sh` memakai entry point kanonis `app.main:app`.
- Tidak ada database pengguna/prod yang dihubungkan, tidak ada migrasi dijalankan, dan tidak ada seeder/smoke check yang dijalankan.

## Verifikasi

- Kompilasi sintaks Python lulus.
- Pemindaian statis tidak menemukan Supabase SDK/PostgREST queries dalam source Python executable (`app/`, `backend/`, `scripts/`, seeder root, dan tests), ataupun dependencies aktif.
- Tes belum dapat berjalan karena `passlib` tidak tersedia; instalasi gagal akibat package index tidak dapat dijangkau. `psycopg` juga tidak tersedia, sehingga query direct-PostgreSQL dan koneksi belum diuji runtime.
- Rincian temuan, gap, rekomendasi, serta sumber teknis tercantum di `BACKEND_AUDIT_RESEARCH.md`.
