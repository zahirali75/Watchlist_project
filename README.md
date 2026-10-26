# CineList — Backend API

REST API untuk katalog film dan watchlist pribadi (proyek mata kuliah Web Application Development).
Dibangun dengan **FastAPI + PostgreSQL**, struktur **per fitur**, tanpa Supabase SDK/PostgREST.

| Fitur | Ringkas |
|---|---|
| Auth | Registrasi, login, JWT (HS256), password PBKDF2-SHA256 600.000 rounds |
| Movies | Katalog film (baca publik, ubah khusus admin), pencarian, filter genre, pagination |
| Watchlists | Watchlist pribadi per user (tambah, ubah status/catatan, hapus, statistik) |
| Users | Daftar/detail/statistik user (khusus admin) |
| Audit Logs | Catatan registrasi dan perubahan katalog (khusus admin) |

## Persyaratan
- Python 3.11 atau 3.12 (teruji di 3.12)
- PostgreSQL 13+ (fungsi `gen_random_uuid()` bawaan). Boleh lokal, atau database Postgres di layanan cloud (termasuk Supabase **sebagai server Postgres saja**).

> Menghapus Supabase SDK **tidak memindahkan lokasi database**. Jika `DATABASE_URL` Anda menunjuk ke host Supabase, data tetap di Supabase; yang berubah hanya cara aplikasi mengaksesnya (SQL langsung, bukan REST API).

## Instalasi cepat
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # lalu isi DATABASE_URL dan SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"   # contoh nilai SECRET_KEY

alembic upgrade head               # membuat semua tabel
./run.sh                           # atau: uvicorn app.main:app --reload --port 8000
```
Swagger UI: <http://localhost:8000/docs> (dimatikan bila `APP_ENV=production`).

## Konfigurasi (`.env`)
Lihat `.env.example`. Wajib: `DATABASE_URL`, `SECRET_KEY` (≥ 32 karakter). Aplikasi **menolak start** bila salah/kurang. `CORS_ORIGINS` berisi daftar origin frontend dipisah koma (tidak boleh `*`).

## Migrasi database
Satu sumber kebenaran: **Alembic** (`migrations/versions/`).
```bash
alembic upgrade head      # database baru / kosong
alembic current           # versi sekarang
alembic downgrade -1      # mundur satu revision
alembic check             # model SQLAlchemy == skema database?
```
Database lama yang dibuat dari file SQL (`migrations/legacy_sql/`): jalankan `alembic stamp 0002`, tinjau revision `0003`, lalu `alembic upgrade head`. Detail: [docs/database.md](docs/database.md).

## Mengisi data film (opsional)
```bash
# butuh TMDB_API_KEY di .env
python scripts/seed_movies.py
```

## Menjalankan tes
```bash
pytest -q                          # unit + API (tanpa database): cepat
# Tes integrasi ke PostgreSQL asli (WAJIB database khusus tes, nama mengandung "test"):
createdb cinelist_test
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/cinelist_test pytest -q
```
Tes integrasi menghapus dan membuat ulang schema `public` di database tes tersebut; tes menolak jalan bila nama database tidak mengandung `test`.

## Struktur folder
```text
app/
├── main.py                 # merakit app: middleware, router, error handler
├── core/                   # config, security (JWT/hash), exceptions, error_handlers,
│                           # logging, pagination, rate_limit, constants
├── db/                     # session.py (engine), executor.py (SQL helper), base.py, models/
├── auth/                   # router, service, schemas, dependencies (get_current_user, require_admin)
├── users/                  # router, service, repository
├── movies/                 # router, service, repository, schemas
├── watchlists/             # router, service, repository, schemas
├── audit_logs/             # router, service, repository, schemas
└── health/                 # router, service, repository
migrations/                 # Alembic (env.py, versions/) + legacy_sql/ (arsip)
tests/                      # unit/, api/, integration/
scripts/                    # seed_movies.py, smoke_check.py
docs/                       # architecture, api, database, erd, frontend-integration, troubleshooting, audit-report
backend/                    # shim kompatibilitas -> app.main (bukan backend kedua)
```
Alur request: `router → service → repository → db/executor → PostgreSQL`. Penjelasan: [docs/architecture.md](docs/architecture.md).

## Dokumentasi
[architecture](docs/architecture.md) · [api](docs/api.md) · [database](docs/database.md) · [erd](docs/erd.md) · [frontend-integration](docs/frontend-integration.md) · [troubleshooting](docs/troubleshooting.md) · [audit-report](docs/audit-report.md)

## Membuat akun admin
Registrasi publik selalu menghasilkan role `user`. Admin dibuat oleh operator tepercaya langsung di database (jangan simpan password admin di repo):
```sql
UPDATE users SET role = 'admin' WHERE email = 'email-anda@example.com';
```
Perubahan role langsung berlaku di request berikutnya (role dibaca dari database, bukan dari token).
