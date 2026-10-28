# Troubleshooting

Cara cepat menemukan fitur bermasalah: **lihat nama logger di log** (`[app.auth]`, `[app.movies]`, `[app.watchlists]`, `[app.db]`, ...), lalu buka folder fitur tersebut.

| Gejala | Kemungkinan penyebab | File yang diperiksa | Langkah diagnosis |
|---|---|---|---|
| Server gagal start, `ValidationError` | `.env` kurang/salah (`DATABASE_URL`, `SECRET_KEY` < 32 karakter, `CORS_ORIGINS=*`) | `app/core/config.py`, `.env` | Baca daftar field yang dikeluhkan di traceback |
| `ModuleNotFoundError` | Dependency belum terpasang / virtualenv salah | `requirements.txt` | `pip install -r requirements.txt`; jalankan dari root proyek |
| Semua endpoint data → 502 `UPSTREAM_ERROR` | Database mati / `DATABASE_URL` salah / password salah | `app/db/session.py`, `app/db/executor.py` | `GET /health/db`; cek log `[app.db]`; coba `psql "$DATABASE_URL"` |
| Koneksi ke Supabase timeout/gagal | Host direct hanya IPv6 | `.env` | Pakai connection string **Session pooler** |
| `relation "users" does not exist` | Migrasi belum dijalankan | `migrations/` | `alembic upgrade head` |
| `alembic` error "Target database is not up to date" | Database lama dibuat dari SQL | `migrations/versions/` | `alembic stamp 0002` lalu upgrade (lihat docs/database.md) |
| Migrasi 0003 berhenti "email kembar" | Ada email sama beda huruf besar/kecil | tabel `users` | Rapikan data, ulangi |
| 401 "Token tidak disertakan" | Header `Authorization: Bearer ...` tidak terkirim | klien frontend | Periksa tab Network |
| 401 "Token kedaluwarsa/tidak valid" | Token lama; `SECRET_KEY` berubah | `app/core/security.py`, `app/auth/dependencies.py` | Login ulang; cek `exp` di jwt.io (jangan tempel token produksi) |
| 401 "User tidak ditemukan" | User dihapus setelah token terbit | tabel `users`, `app/auth/dependencies.py` | Registrasi/login ulang |
| 401 padahal password benar | Hash tidak cocok / salah email | `app/auth/service.py` | Cek log `[app.auth]` "Login gagal" |
| 429 saat login | Terlalu banyak gagal (`LOGIN_MAX_ATTEMPTS` per `LOGIN_WINDOW_SECONDS`) | `app/core/rate_limit.py` | Tunggu `retryAfterSeconds`; reset = restart server |
| 403 di endpoint admin | Role bukan admin **di database** | `app/auth/dependencies.py` | `SELECT role FROM users WHERE email=...` |
| 403 di watchlist | Item milik user lain | `app/watchlists/service.py` (`_get_owned_item`) | Bandingkan `user_id` item dengan user login |
| 404 data tidak ada | ID salah / data terhapus | `repository.py` fitur terkait | Cek langsung di database |
| 409 duplikat | Email / film sudah ada di watchlist | `service.py`, constraint UNIQUE | Bukan bug; tampilkan pesan ke user |
| 422 | Body tidak sesuai skema | `schemas.py` fitur | Baca `data.errorMeta[].location` |
| 400 "limit maksimal 100" | `limit` terlalu besar | `app/core/pagination.py` | Kecilkan `limit` |
| Browser: "blocked by CORS" / fetch gagal total ("API tidak bisa dijangkau") | Origin frontend belum terdaftar di `CORS_ORIGINS` | `CORS_ORIGINS` di `.env`, `app/main.py` | **Cek port frontend yang sebenarnya** (console: `location.origin`). Vite otomatis pindah ke **5174** bila 5173 terpakai — origin 5174 harus terdaftar juga. Perhatikan `localhost:5174` ≠ `127.0.0.1:5174`: browser menganggapnya origin BERBEDA, daftarkan keduanya. Tambah origin persis (skema+host+port), restart server. |
| Frontend jalan tapi "API tidak bisa dijangkau", padahal `curl /health/db` = 200 | Backend lama (kode usang) masih memegang port 8000; proses `--reload` basi menutupi kode terbaru | Proses uvicorn ganda | Cek jumlah listener: `netstat -ano \| findstr :8000` (harus SATU PID). Bandingkan rute: `curl -s localhost:8000/openapi.json \| findstr /c:"/reviews"` — hilang = menjalankan kode lama. Matikan semua lalu jalankan `./run.sh` sekali saja. |
| `/docs` 404 | `APP_ENV=production` | `app/main.py` | Gunakan `APP_ENV=development` |
| Frontend salah baca response | Kontrak berbeda dari dugaan | `docs/api.md`, `schemas.py`, `router.py` | Bandingkan dengan `/openapi.json` & contoh di api.md |
| 500 `INTERNAL_ERROR` | Bug tak terduga | Log server | Cari traceback `Unhandled error pada <METHOD> <path>` → file fitur sesuai path |
| Tes integrasi: "Ditolak: database ... bukan database tes" | Pengaman aktif | `tests/integration/conftest.py` | Pakai database yang namanya mengandung `test` |
| `pytest` error import `passlib`/`jwt` | Dependency tes belum terpasang | `requirements.txt` | `pip install -r requirements.txt` |

Perintah berguna:
```bash
pytest tests/api/test_<fitur>.py -q      # isolasi satu fitur
alembic current && alembic check         # status migrasi & kesesuaian model
curl -s localhost:8000/health/db         # cek database
```
