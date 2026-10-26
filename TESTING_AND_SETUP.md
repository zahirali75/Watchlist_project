# Setup, Migrasi, dan Testing — CineList

Semua langkah di bawah sudah dijalankan dan diverifikasi pada Python 3.12.3 dan PostgreSQL 16.15.

## 1. Prasyarat

- Python 3.11 atau 3.12 (diuji pada 3.12.3). Python 3.13 belum diuji dan passlib memberi peringatan untuk itu.
- PostgreSQL 13 atau lebih baru (diuji pada 16.15). Diperlukan fungsi `gen_random_uuid()`.

## 2. Instalasi dependency

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Versi yang terpasang saat pengujian: fastapi 0.162.0, sqlalchemy 2.1.6, pydantic 2.14.1, psycopg 3.3.6, PyJWT 2.15.1, passlib 1.7.4, alembic 1.20.1, uvicorn 0.54.0, pytest 9.1.1, httpx 0.28.1.

`requirements.txt` memakai batas bawah (`>=`), jadi instalasi baru dapat memakai versi yang lebih baru dari yang diuji.

## 3. Konfigurasi environment

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # salin hasilnya ke SECRET_KEY
```

| Variabel | Wajib | Keterangan |
|---|---|---|
| `DATABASE_URL` | ya | `postgresql+psycopg://user:password@host:5432/nama_db` |
| `SECRET_KEY` | ya | Minimal 32 karakter. Aplikasi menolak start bila nilainya masih berupa contoh (`replace_...`, `your_...`, `changeme`, `example`). |
| `ALGORITHM` | tidak | Hanya `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | tidak | Default 60. |
| `LOGIN_MAX_ATTEMPTS` | tidak | Default 5 per (IP + email). |
| `LOGIN_IP_MAX_ATTEMPTS` | tidak | Default 50 per IP. |
| `LOGIN_WINDOW_SECONDS` | tidak | Default 300. |
| `APP_ENV` | tidak | `development` atau `production`. Production mematikan `/docs`. |
| `CORS_ORIGINS` | tidak | Dipisah koma. Tidak boleh `*`. |
| `TMDB_API_KEY` | tidak | Hanya untuk seeder. |
| `TEST_DATABASE_URL` | tidak | Hanya untuk tes integrasi. Nama database harus mengandung `test`. |

`.env` tidak boleh masuk Git atau ZIP distribusi. `.gitignore` sudah mengecualikannya.

## 4. Setup database

Buat database dan pengguna (contoh lokal):

```bash
sudo -u postgres psql -c "CREATE USER cinelist_user WITH PASSWORD 'ganti_dengan_password_kuat';"
sudo -u postgres createdb -O cinelist_user cinelist
```

Pengguna sebaiknya tidak superuser. Pengujian integrasi membutuhkan izin membuat ulang schema `public` di database tes.

## 4b. Catatan khusus Supabase

Jika `DATABASE_URL` menunjuk ke Supabase:

- Gunakan **Session pooler** (lihat `.env.example`). Transaction pooler (port 6543) belum diuji dan driver psycopg memakai prepared statement yang bisa bermasalah di mode itu.
- Backend ini **tidak** memakai Supabase Auth, SDK, atau PostgREST. Jangan memasukkan kunci `anon` atau `service_role` Supabase ke frontend atau `.env` backend untuk akses data.
- Migrasi 0004 mengamankan Data API. Periksa peran aplikasi dan verifikasi hak akses setelah migrasi (lihat `DATABASE_ERD.md` bagian 5b).
- Staging dulu: jalankan migrasi di database non-produksi, lalu cek Data API settings di dashboard (tabel baru tidak selalu terbuka otomatis, tetapi jangan mengandalkan itu).

## 5. Migrasi

```bash
alembic upgrade head      # database baru
alembic current           # harus menampilkan 0004 (head)
alembic check             # harus: No new upgrade operations detected
```

Database yang dibuat dari file SQL lama (`migrations/legacy_sql/`): `alembic stamp 0002`, tinjau revision `0003` dan `0004`, lalu `alembic upgrade head`. Backup database dulu.

## 6. Seed data (opsional)

```bash
# .env harus berisi TMDB_API_KEY
python scripts/seed_movies.py
```

Seeder mengambil 20 film populer dan memasukkannya tanpa pengecekan duplikat. Jalankan sekali per database.

## 7. Menjalankan server

```bash
./run.sh                                           # Linux/macOS/Git Bash
# atau
uvicorn app.main:app --reload --port 8000
```

Verifikasi:

```bash
curl http://localhost:8000/health        # {"success": true, ...}
curl http://localhost:8000/health/db     # database terhubung
```

Swagger: `http://localhost:8000/docs` (development saja).

## 8. Menjalankan test

### Unit dan API (tanpa database)

```bash
pytest -q
```

Hasil saat audit: **80 lulus, 17 dilewati**. Tes integrasi dilewati karena `TEST_DATABASE_URL` belum diisi.

### Integrasi (PostgreSQL asli)

```bash
createdb -O cinelist_user cinelist_test
TEST_DATABASE_URL=postgresql+psycopg://cinelist_user:password@127.0.0.1:5432/cinelist_test pytest -q
```

Hasil saat audit: **97 lulus**.

PERINGATAN: tes integrasi menghapus dan membuat ulang schema `public` di database tes. Pengaman menolak jalan bila nama database tidak mengandung `test`. Jangan pernah mengarahkannya ke database produksi.

### Analisis statis

```bash
pip install pyflakes
python -m pyflakes app tests scripts seed_movies.py backend
```

Hasil saat audit: tidak ada temuan.

### Smoke test (server berjalan)

```bash
python scripts/smoke_check.py
```

Script ini membuat satu akun uji di database target. Jalankan hanya ke database pengembangan.

## 9. Hasil aktual

| Pemeriksaan | Perintah | Hasil |
|---|---|---|
| Unit + API | `pytest -q` | 80 lulus, 17 dilewati |
| Integrasi + semua | `TEST_DATABASE_URL=... pytest -q` | 97 lulus |
| Migrasi dari kosong | `alembic upgrade head` | Berhasil (0001 → 0003) |
| Drift model | `alembic check` | Tidak ada drift |
| Analisis statis | `pyflakes` | Bersih |
| Smoke server | `scripts/smoke_check.py` | Sesuai ekspektasi (401, 403, 409, 200, 201) |
| Serangan JWT dan input | probe manual terhadap server | Semua ditolak sesuai desain |

Belum diuji: deployment produksi, database Supabase, beban tinggi, dan multi-worker.

## 10. Troubleshooting

| Gejala | Penyebab umum | Solusi |
|---|---|---|
| `SECRET_KEY masih berupa nilai contoh` | `.env` masih berisi contoh | Isi dengan hasil `secrets.token_urlsafe(48)` |
| `Field required ... DATABASE_URL` | `.env` tidak dibaca | Pastikan file `.env` ada di folder project, bukan di subfolder |
| `connection refused` ke 5432 | PostgreSQL belum berjalan | Jalankan service PostgreSQL, cek port |
| `password authentication failed` | Kredensial salah atau pengguna belum dibuat | Periksa `DATABASE_URL` dan jalankan ulang `CREATE USER` |
| Koneksi Supabase timeout di IPv4 | Host direct hanya IPv6 | Gunakan connection string **Session pooler** |
| `Migrasi 0003 dihentikan: ada email kembar` | Ada email sama beda huruf besar | Rapikan data lalu jalankan `alembic upgrade head` lagi |
| `Migrasi 0004 dihentikan: role ... bukan pemilik tabel` | Migrasi dijalankan oleh peran non-pemilik tanpa BYPASSRLS | Jalankan migrasi dengan peran pemilik tabel, atau beri BYPASSRLS ke peran tersebut |
| Semua query mengembalikan kosong setelah 0004 | Peran aplikasi bukan pemilik tabel dan tidak memiliki BYPASSRLS | Periksa `rolbypassrls` dan `tableowner` (lihat `DATABASE_ERD.md` bagian 5b) |
| Frontend kena error CORS | Origin tidak ada di `CORS_ORIGINS` | Tambahkan origin, restart server |
| Login terus 429 | Batas per email atau per IP tercapai | Tunggu `retryAfterSeconds`, atau naikkan `LOGIN_*` di `.env` |
| Tes integrasi menolak jalan | Nama database tidak mengandung `test` | Gunakan database seperti `cinelist_test` |
| `pytest` gagal `Connection refused` di tes integrasi | Database tes mati | Nyalakan PostgreSQL atau kosongkan `TEST_DATABASE_URL` untuk tes tanpa database |
