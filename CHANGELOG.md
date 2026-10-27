# CHANGELOG — Audit dan Hardening Backend CineList

Perbandingan terhadap kode sebelum audit (snapshot dari ZIP yang diunggah). Versi API tetap `2.0.0`.

## Sesi & password (27 Oktober 2026)

Empat penambahan yang menutup celah terakhir sebelum frontend dibangun. Bentuk respons lama **tidak diubah** — tes kontrak tetap menegakkannya.

- **Sesi berlapis (refresh token).** Sebelumnya JWT berlaku 60 menit tanpa jalur perpanjangan, sehingga pengguna terlempar ke halaman login di tengah pemakaian. Sekarang tabel `refresh_tokens` (migrasi 0005) menyimpan sesi 14 hari; token **hanya disimpan sebagai hash SHA-256**, jadi bocornya isi tabel tidak memberi akses. Token **dirotasi** tiap dipakai. (`POST /auth/refresh`, `POST /auth/logout`)
- **Profil sendiri** `GET/PUT /users/me`. Sebelumnya satu-satunya jalur data user adalah endpoint admin, sehingga pengguna biasa **selalu 403** bahkan untuk datanya sendiri. Router `/users/me` dipisah dari router admin (yang dijaga menyeluruh) dan didaftarkan lebih dulu agar tidak tertangkap pola `/users/{user_id}`.
- **Ganti password** `POST /auth/change-password` (wajib password lama; seluruh sesi dicabut) dan **lupa password** lewat email: `POST /auth/forgot-password` + `POST /auth/reset-password`. Tabel `password_resets` (migrasi 0006) menyimpan token sekali pakai berumur 30 menit, juga sebagai hash. Jawaban lupa password **selalu sama** sehingga tidak membocorkan email mana yang terdaftar.
- **Email dikirim lewat `app/notifications/`.** Bila `SMTP_HOST` kosong, email tidak dikirim dan isinya hanya ditulis ke log server — jalur lupa password tetap bisa diuji saat pengembangan.
- **Tes integrasi dijalankan sungguhan** (17 tes, sebelumnya 17 dilewati): dibuat database `cinelist_test` terpisah karena tes ini menghapus schema `public`. Ditemukan dan diperbaiki: (1) `alembic check` mendeteksi model `refresh_token`/`password_reset` tidak sinkron dengan migrasi (unique lewat `unique=True` di kolom vs unique index) — model disamakan dengan migrasi; (2) `connect_timeout` ditambahkan di `app/db/session.py`, sebab tanpa itu koneksi ke host yang tidak menjawab **menggantung tanpa batas** alih-alih gagal cepat; (3) `python-dotenv` (sudah ada di requirements) kini dimuat `tests/conftest.py` agar `TEST_DATABASE_URL` dari `.env` terbaca.
- Hasil: `pytest` **122 lulus / 1 dilewati** (tes ownership role dilewati khusus di Supabase — pooler-nya butuh SNI/external_id untuk multi-role). Endpoint: **28 operasi** (sebelumnya 20).

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
- **Sudah diverifikasi** terhadap Supabase nyata pada 26 Okt 2026: RLS aktif di keempat tabel, grant `anon`/`authenticated` = 0 tabel dan 0 usage schema, dan `alembic check` tanpa drift. Catatan: pada proyek Supabase baru grant itu memang sudah kosong, sehingga 0004 berperan sebagai lapis penegas, bukan perbaikan kebocoran.

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
- **26 Okt 2026, dijalankan ulang pada Supabase PostgreSQL 17.6:** 82 lulus + 17 dilewati. 17 yang dilewati ada di `tests/integration` dan hanya jalan bila `TEST_DATABASE_URL` diisi database tes terpisah.
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
