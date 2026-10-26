# CHANGELOG — Audit dan Hardening Backend CineList

Perbandingan terhadap kode sebelum audit (snapshot dari ZIP yang diunggah). Versi API tetap `2.0.0`.

## Keamanan

- **Placeholder `SECRET_KEY` ditolak.** Sebelumnya nilai contoh dari `.env.example` (62 karakter) diterima. Sekarang aplikasi menolak start dengan pesan yang jelas. (`app/core/config.py`)
- **Algoritma JWT dikunci.** `ALGORITHM` bertipe `Literal["HS256"]`. (`app/core/config.py`)
- **Klaim `exp` dan `sub` wajib pada token.** Token tanpa `exp` yang ditandatangani dengan secret benar sebelumnya diterima. (`app/core/security.py`)
- **Throttle login per IP lintas email.** Setelah `LOGIN_IP_MAX_ATTEMPTS` (default 50) kegagalan dalam `LOGIN_WINDOW_SECONDS` dari satu IP, semua login dari IP tersebut mendapat 429. Throttle per (IP + email) tetap ada. (`app/core/rate_limit.py`, `app/auth/service.py`)
- **Bucket throttle kosong dibuang.** Mencegah pertumbuhan memori tanpa batas. (`app/core/rate_limit.py`)
- **`poster_url` hanya http/https atau kosong.** Mencegah `javascript:` dan `data:` tersimpan. (`app/movies/schemas.py`)

## Supabase (migrasi 0004)

- **RLS aktif** di `users`, `movies`, `watchlists`, `audit_logs`. Tanpa policy, peran non-pemilik tidak melihat baris. (`migrations/versions/0004_supabase_exposure_hardening.py`)
- **Grant ke `anon` dan `authenticated` dicabut** dari tabel dan sequence `public`, beserta default privilege, bila peran tersebut ada. Mencegah paparan lewat Data API. Tidak berpengaruh di PostgreSQL biasa.
- **Pemeriksaan awal migrasi:** berhenti dengan pesan jelas bila peran yang menjalankan migrasi bukan pemilik tabel dan tidak memiliki BYPASSRLS.
- **Downgrade** hanya mematikan RLS. Grant tidak dikembalikan secara otomatis.
- Tes baru: 4 di `tests/integration/test_supabase_exposure.py`. Dibuktikan: menghapus `ENABLE ROW LEVEL SECURITY` membuat 2 tes gagal; menghapus guard membuat 1 tes gagal.
- Panduan Supabase: `TESTING_AND_SETUP.md` bagian 4b. Pemeriksaan skill: `BACKEND_DEEP_AUDIT_REPORT.md` bagian 9b. Verifikasi peran: `DATABASE_ERD.md` bagian 5b.
- **Belum diverifikasi** terhadap Supabase nyata. Akses ke supabase.com, CLI, dan dashboard tidak tersedia di lingkungan audit.

## Validasi input

- `overview` maksimal 10.000 karakter; `poster_url` maksimal 2.048.
- `notes` watchlist maksimal 2.000 karakter. (`app/watchlists/schemas.py`)
- `page` maksimal 1.000.000 (sebelumnya tanpa batas atas, `page=2^63` menghasilkan error database). (`app/core/pagination.py`)

## Format error dan kebocoran detail

- Rute tidak ada (404) dan metode tidak didukung (405) memakai envelope seragam `{success, message, data.errorCode}`. Sebelumnya memakai `{"detail": ...}` dari FastAPI. (`app/core/error_handlers.py`)
- `GET /users/{id}` dan `GET /users/{id}/stats` dengan id bukan UUID menghasilkan 404 tanpa menyentuh database. Sebelumnya 400 dengan pesan tipe database. (`app/users/service.py`)

## Konfigurasi dan dokumentasi

- `GET /` di production mengembalikan JSON, bukan redirect ke `/docs` yang sudah dimatikan. Field `data.docs` di `/health` bernilai `null` di production. (`app/health/router.py`)
- `LOGIN_IP_MAX_ATTEMPTS` ditambahkan ke `.env.example`, dengan peringatan bahwa placeholder ditolak.
- `docs/api.md` diperbarui: aturan input baru, format error, batas login, dan keputusan enumerasi email.
- `migrations/legacy_sql/README.md` diperbaiki: tidak lagi merujuk folder `alembic/` yang sudah tidak ada, dan path arsip yang benar.

## Kebersihan kode

- Import tak terpakai dihapus dari `app/movies/router.py`. Pyflakes sekarang bersih untuk `app`, `tests`, `scripts`, `seed_movies.py`, dan `backend`.

## Tes

- Tes baru: 19 (`tests/unit/test_config.py` +2, `tests/unit/test_security.py` +2, `tests/unit/test_rate_limit.py` +2, `tests/api/test_hardening.py` baru dengan 9 tes).
- Hasil: 80 lulus + 17 dilewati tanpa database (sebelumnya 65 + 13). 97 lulus dengan PostgreSQL 16.15 (sebelumnya 78).
- 14 dari 15 tes baru dibuktikan gagal di kode asli. Tes batas `page` ditambahkan belakangan dan belum diuji terhadap kode asli.

## Daftar file yang berubah

| File | Jenis | Alasan |
|---|---|---|
| `app/core/config.py` | diubah | Placeholder ditolak, HS256 dikunci, `LOGIN_IP_MAX_ATTEMPTS`, `ACCESS_TOKEN_EXPIRE_MINUTES >= 1` |
| `app/core/security.py` | diubah | Wajibkan `exp` dan `sub` |
| `app/core/rate_limit.py` | diubah | Key per IP, pembuangan bucket kosong |
| `app/core/error_handlers.py` | diubah | Envelope untuk HTTP error framework |
| `app/core/pagination.py` | diubah | Batas atas `page` |
| `app/auth/service.py` | diubah | Throttle per IP |
| `app/movies/schemas.py` | diubah | Validasi `poster_url`, batas `overview` |
| `app/movies/router.py` | diubah | Hapus import tak terpakai |
| `app/watchlists/schemas.py` | diubah | Batas `notes` |
| `app/users/service.py` | diubah | Validasi UUID sebelum query |
| `app/health/router.py` | diubah | Perilaku production untuk `/` dan `docs` |
| `.env.example` | diubah | Variabel baru dan peringatan placeholder |
| `docs/api.md` | diubah | Kontrak baru |
| `migrations/legacy_sql/README.md` | diubah | Path dan status Alembic yang benar |
| `tests/unit/test_config.py` | diubah | +2 tes |
| `tests/unit/test_security.py` | diubah | +2 tes |
| `tests/unit/test_rate_limit.py` | diubah | +2 tes |
| `tests/api/test_hardening.py` | baru | 9 tes |
| `migrations/versions/0004_supabase_exposure_hardening.py` | baru | Pengamanan paparan Data API |
| `tests/integration/test_supabase_exposure.py` | baru | 4 tes pengamanan Supabase |
| `BACKEND_DEEP_AUDIT_REPORT.md` | baru | Laporan audit |
| `FRONTEND_API_INTEGRATION.md` | baru | Panduan integrasi |
| `DATABASE_ERD.md` | baru | Dokumentasi database |
| `TESTING_AND_SETUP.md` | baru | Setup dan testing |
| `CHANGELOG.md` | baru | Daftar perubahan ini |

Perubahan skema: hanya migrasi 0004 yang mengatur RLS dan grant, tanpa perubahan kolom, tabel, atau data. Path endpoint, nama field, dan format sukses tidak berubah.

## Tidak diubah dengan sengaja

- Registrasi tetap mengembalikan 409 dengan email di `errorMeta` (keputusan produk).
- Admin tetap tidak bisa membaca watchlist user lain.
- `backend/`, `seed_movies.py` di root, `migrations/legacy_sql/`, dan `docs/archive/` tetap ada sebagai kompatibilitas dan arsip.
- passlib tetap dipakai (tercatat sebagai risiko di laporan audit).

## Perubahan yang belum dikerjakan

Lihat bagian 11 pada `BACKEND_DEEP_AUDIT_REPORT.md`.
