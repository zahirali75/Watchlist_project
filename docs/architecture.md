# Arsitektur

## Alur satu request
```text
HTTP Request
  → router.py        terima request, pasang dependency, tentukan status code
  → schemas.py       validasi input (Pydantic) → 422 bila salah
  → dependencies     auth/dependencies.py: JWT → cek user di DB → role terkini
  → service.py       aturan bisnis (ownership, duplikat, 404/403/409)
  → repository.py    SQL terparameter
  → db/executor.py   eksekusi + terjemah error database → exception domain
  → PostgreSQL
Response kembali: repository → service → router → JSON
Error: exception domain (core/exceptions.py) → core/error_handlers.py → JSON seragam
```

## Tanggung jawab tiap bagian
| Bagian | Tugas | Tidak boleh |
|---|---|---|
| `router.py` | HTTP, dependency, status code, bentuk response | SQL, aturan bisnis |
| `schemas.py` | Bentuk & validasi data | akses database |
| `service.py` | Aturan bisnis, orkestrasi | SQL, objek HTTP |
| `repository.py` | Satu-satunya tempat SQL fitur tersebut | aturan bisnis |
| `core/` | Config, keamanan, error, logging, pagination, rate limit | logika fitur |
| `db/` | Engine, executor SQL, model skema (Alembic) | logika fitur |

## Hubungan antar fitur
```text
auth ──▶ users.service           (cari/buat user, ganti hash)
auth ──▶ audit_logs.service      (catat registrasi)
movies ─▶ audit_logs.service     (catat CRUD film)
watchlists ─▶ movies.service     (pastikan film ada)
users ─▶ watchlists.service      (statistik user)
semua fitur ─▶ auth.dependencies (get_current_user / require_admin)
```
Aturan (dijaga otomatis oleh `tests/unit/test_architecture.py`): fitur hanya boleh mengimpor `service`, `schemas`, atau `dependencies` milik fitur lain — tidak pernah `repository`. SQL hanya di `repository.py`; `router.py` tidak mengimpor repository.

`auth` tidak punya `repository.py` karena tidak punya tabel sendiri: data user dikelola fitur `users`. Berkas kosong sengaja tidak dibuat.

## Database
`db/session.py` membuat satu engine SQLAlchemy (pool koneksi) dari `DATABASE_URL`. Query ditulis sebagai SQL biasa dengan parameter bernama (`:nama`) — aman dari SQL injection; nama kolom dinamis (UPDATE) dibatasi allowlist. Model di `db/models/` hanya mendeskripsikan skema untuk Alembic.

## Logging
`core/logging.py`. Logger per fitur: `app.auth`, `app.users`, `app.movies`, `app.watchlists`, `app.audit_logs`, `app.db`, `app.core`. Nama logger di log langsung menunjukkan fitur yang bermasalah. Password, token, dan secret tidak dicatat.

## Legacy
`backend/main.py` dan `backend/database.py` adalah **shim kompatibilitas**: hanya mengekspor `app.main:app` dan koneksi aktif, sehingga perintah lama `uvicorn backend.main:app` menjalankan aplikasi yang sama. Tidak ada backend kedua. Entry point resmi: `app.main:app`.
