# Laporan Deep Audit & Refactor Backend CineList

Tanggal: 24 Oktober 2026 · Basis: `Watchlist_project_per_fitur.zip` (diverifikasi **identik** dengan hasil refactor sebelumnya; ZIP asli tidak diubah) · Hasil: `Watchlist_Project_Refactored.zip`

Legenda status: **[T]** Terverifikasi (bukti dari kode/tes) · **[I]** Indikasi · **[B]** Belum diverifikasi · **[✔]** Sudah diperbaiki · **[✘]** Belum diperbaiki.

## 1. Ringkasan eksekutif
Backend sudah berfungsi baik sebagai MVP/proyek kuliah. Pada audit ini struktur diratakan ke target per fitur, Alembic dijadikan sumber kebenaran skema (sebelumnya kosong), dan beberapa celah keamanan serta kontrak API diperbaiki. Seluruh perubahan diuji: **65 tes tanpa database + 13 tes integrasi ke PostgreSQL asli = 78 lulus, 0 gagal**, server dijalankan sungguhan, migrasi diuji dari database kosong. **Belum** diuji terhadap database Supabase/produksi Anda dan **belum** ada frontend nyata. Aplikasi **belum layak dinyatakan siap produksi** (lihat bagian 11).

## 2. Struktur awal → akhir
Awal (hasil refactor sebelumnya): `app/features/<fitur>/…`, `app/core/deps.py`, `app/db/{session,client,…}`, `alembic/` (kosong) + `migrations/*.sql`, `tests/{core,features}`.
Akhir:
```text
app/ main.py · core/{config,security,exceptions,error_handlers,logging,pagination,rate_limit,constants}
     db/{session,executor,base}.py + models/{user,movie,watchlist,audit_log}
     auth/{router,service,schemas,dependencies} · users/{router,service,repository}
     movies/ · watchlists/ · audit_logs/ (router,service,repository,schemas) · health/{router,service,repository}
migrations/ env.py · versions/{0001,0002,0003} · legacy_sql/ (arsip)
tests/ unit/ · api/ · integration/ · scripts/ · docs/ · backend/ (shim)
```
Keputusan struktur: mengikuti target Anda (fitur langsung di bawah `app/`). Perbedaan yang disengaja: `auth` tanpa `repository.py` (tidak punya tabel; memakai `users.service`), tanpa `Dockerfile`/`pyproject.toml` (belum diimplementasikan; tidak dibuat sebagai berkas kosong), `health/` ditambahkan, `db/executor.py` ditambahkan, `watchlist` → `watchlists` (nama folder; URL tidak berubah).

## 3. File dipindah / diubah / ditambah / legacy
**Dipindah**: `app/features/{auth,users,movies,audit_logs,health}` → `app/…`; `features/watchlist` → `app/watchlists`; `core/deps.py` → `auth/dependencies.py`; `repositories/base.py` → `db/executor.py` (sebelumnya); `alembic/{env.py,script.py.mako}` → `migrations/`; `migrations/000{1,2}*.sql`, `schema.sql`, `migrations/README.md` → `migrations/legacy_sql/`; `tests/core/*` → `tests/unit/`; `tests/features/*` → `tests/api/`; `ARCHIVE_AUDIT.md`, `COMPARISON.md`, `BACKEND_AUDIT_RESEARCH.md`, `backend/database_schema.md` → `docs/archive/`.
**Diubah**: `app/main.py`, `core/{config,exceptions}.py`, `db/session.py`, `auth/{router,service}.py`, `users/{router,service,repository}.py`, `watchlists/service.py`, `health/router.py`, `migrations/env.py`, `alembic.ini`, `run.sh`, `.env.example`, `.gitignore`, `scripts/smoke_check.py`, `seed_movies.py`, `tests/conftest.py`, semua import.
**Ditambah**: `core/{logging,rate_limit}.py`, `db/base.py`, `db/models/*`, `health/{repository,service}.py`, `migrations/versions/000{1,2,3}_*.py`, 7 file tes baru, `docs/*`.
**Dihapus**: `app/db/client.py` (shim duplikat), `app/api/`, `app/services/`, `app/repositories/`, `app/schemas/` (isinya sudah pindah), `alembic/versions/.gitkeep`.
**Dipertahankan sebagai legacy**: `backend/main.py`, `backend/database.py` (shim → app aktif), `migrations/legacy_sql/*`, `docs/archive/*`, `seed_movies.py` di root (kini pembungkus tipis ke `scripts/seed_movies.py`; sebelumnya implementasi ganda), `.git/` utuh.

## 4. Endpoint sebelum vs sesudah
Dibandingkan otomatis dari OpenAPI kedua versi: **19 → 20**. Hilang: **tidak ada**. Ditambah: `GET /health/db` (readiness; ditandai sebagai penambahan). Alias tersembunyi `POST /login` dan `POST /users` tetap. Snapshot kontrak dikunci di `tests/api/test_contract.py`.
Perubahan perilaku pada endpoint yang ada (semua didokumentasikan di `docs/api.md`):
| Endpoint | Sebelum | Sesudah |
|---|---|---|
| Semua endpoint login | Role dibaca dari token | Role + keberadaan user dibaca dari database → token user terhapus = 401; role dicabut = 403 |
| `POST /auth/login` | Tidak dibatasi | 429 setelah 5 gagal/300 dtk per (IP+email) |
| `GET /users/{id}/stats` | User tak ada → statistik 0 | 404 |
| `PUT /watchlists/{id}` | `notes: null` diabaikan | Menghapus catatan; `status: null` → 400 |
| `/docs`,`/redoc`,`/openapi.json` | Selalu aktif | Mati bila `APP_ENV=production` |
| CORS | methods/headers `*` | Hanya GET/POST/PUT/DELETE/OPTIONS & Authorization/Content-Type; `CORS_ORIGINS=*` ditolak saat boot |

## 5. Temuan keamanan
| # | Temuan | Status |
|---|---|---|
| S1 | Role admin dari JWT, tidak dicek ke DB → token admin lama tetap sakti sampai `exp`; token user yang dihapus tetap valid | [T] [✔] diperbaiki `auth/dependencies.py`; diuji unit + integrasi (cabut role, hapus user) |
| S2 | Tanpa pembatas login | [T] [✔] `core/rate_limit.py`, **in-memory per proses** (multi-worker butuh Redis/proxy) — keterbatasan [✘] |
| S3 | Login email tak dikenal lebih cepat (user enumeration via waktu) | [I] [✔] verifikasi hash palsu; **tidak diukur** secara statistik |
| S4 | `sub` non-UUID menyebabkan error database | [T] [✔] ditolak 401 |
| S5 | CORS terlalu longgar | [T] [✔] |
| S6 | Password: PBKDF2-SHA256 600.000 rounds, hash lama (29.000) tetap valid & di-upgrade saat login | [T] sudah ada; diuji (`test_security.py`) |
| S7 | JWT: algoritma allowlist HS256, `exp` wajib diverifikasi, secret ≥32 karakter dari env, alg `none` ditolak | [T] diuji |
| S8 | `password_hash` tidak muncul di respons `/users` | [T] diuji |
| S9 | Pesan error database tidak bocor ke klien | [T] diuji (integrasi) |
| S10 | Tidak ada refresh token / logout / revoke | [T] [✘] ditunda (tidak ditambah infrastruktur); mitigasi: cek user/role ke DB, masa berlaku 60 mnt |
| S11 | HTTPS, security headers, TrustedHost | [✘] urusan deployment/reverse proxy |
| S12 | Koneksi langsung ke Postgres melewati RLS Supabase | [T] dicatat; otorisasi di kode (ownership diuji) |
| S13 | `passlib` 1.7.4 tidak dipelihara & memunculkan peringatan `crypt` | [T] [✘]; Python 3.13 **belum diuji** |
| S14 | Audit hanya mencatat registrasi & CRUD film; login gagal/perubahan watchlist/akses admin tidak; kegagalan menulis audit hanya di-log | [T] [✘] sesuai desain lama; login gagal masuk log aplikasi (`app.auth`) |

## 6. Temuan database
| # | Temuan | Status |
|---|---|---|
| D1 | Alembic: `target_metadata=None`, tanpa revision | [T] [✔] model + revision 0001–0003; `alembic check` bersih |
| D2 | Revision 0001–0002 identik dengan SQL lama | [T] 49 objek skema sama (kolom, constraint, index) |
| D3 | `role`/`status` nullable meski punya CHECK; `rating`/`tahun` tanpa batas; email kembar beda kapitalisasi | [T] [✔] revision **0003** (baru, terpisah, bisa di-downgrade); teruji di DB kosong & pesan jelas bila ada email kembar. **Belum dijalankan di data nyata** |
| D4 | `TIMESTAMP` vs `TIMESTAMPTZ` campur | [T] [✘] sengaja ditunda (butuh keputusan zona waktu) |
| D5 | `schema.sql` tak punya `audit_logs` | [T] [✔] SQL lama diarsipkan; Alembic = sumber tunggal |
| D6 | Index trigram untuk `ILIKE '%x%'` | [I] [✘] tunda sampai data besar |
| D7 | Transaksi & rollback: tiap operasi tulis = satu transaksi (commit saat sukses, rollback saat error); pelanggaran UNIQUE/FK diterjemahkan ke 409/400. **Tidak ada transaksi lintas operasi** (mis. simpan film lalu tulis audit = dua transaksi terpisah; kegagalan audit tidak membatalkan film, sesuai desain) | [T] diuji integrasi; keterbatasan [✘] |
| D8 | Statistik watchlist = 4 query COUNT | [T] [✘] efisiensi minor |
| D9 | ERD lama memuat tabel tak ada (`reviews`, dll.) | [T] [✔] ERD baru dari skema aktual (`docs/erd.md`) |

## 7. Temuan API / integrasi frontend
- Format error seragam `{"success":false,"message","data":{"errorCode"}}` dipertahankan (bukan `{"detail"}`), diuji. [T]
- `response_model` Pydantic belum dipakai → OpenAPI tidak menampilkan tipe respons. [T] [✘] (menambahkannya berisiko mengubah bentuk respons; ditunda). Mitigasi: kontrak didokumentasikan dari respons asli + tes snapshot endpoint.
- Penamaan campuran `snake_case` (film/watchlist) vs `camelCase` (auth/stats). [T] [✘] dipertahankan demi kompatibilitas.
- `PUT /movies` = penggantian penuh. [T] terdokumentasi.
- Timestamp tanpa zona pada 3 tabel. [T] terdokumentasi.
- Contoh `fetch`/Axios di `docs/frontend-integration.md` memakai bentuk respons asli, tetapi **kode JS-nya tidak dijalankan** (tidak ada frontend). [B]

## 8. Temuan konfigurasi & operasional
- `run.sh` hanya memakai `.venv/Scripts/python.exe` (Windows) → [T] [✔] kini memilih `bin/` atau `Scripts/`; **diuji di Linux**, jalur Windows [B].
- `smoke_check.py` memakai port 8010 dan teks "Supabase" → [T] [✔] default 8000, `BASE_URL`.
- Tes arsitektur menjadi **kosong tanpa disadari** setelah folder `features/` dihapus → [T] [✔] ditemukan saat audit, ditulis ulang berbasis AST dan diberi tes penjaga.
- `health/router.py` pernah memanggil database langsung → [T] [✔] dipisah service/repository.
- Entry point ganda: `backend.main:app` = alias objek yang sama dengan `app.main:app` (diuji `is`). [T]
- Nama variabel: kode memakai `SECRET_KEY` (bukan `JWT_SECRET_KEY` di contoh prompt); **tidak diganti** agar `.env` lama tetap jalan.

## 9. Hasil verifikasi
| Pemeriksaan | Hasil |
|---|---|
| `compileall` app, backend, tests, scripts, migrations | Lulus |
| Import 51 modul + `seed_movies` + shim `backend` | Lulus, tidak ada circular import |
| Tes tanpa DB (`pytest`) | **65 lulus**, 13 dilewati (integrasi, butuh `TEST_DATABASE_URL`), 0 gagal |
| Tes dengan PostgreSQL asli (DB `cinelist_test`) | **78 lulus**, 0 gagal, 0 dilewati |
| Rincian | unit 17 · api 48 · integration 13 |
| Migrasi dari DB kosong → head; `alembic check`; downgrade base → upgrade | Lulus |
| Alembic@0002 vs SQL lama | Identik (49 objek) |
| Server nyata (uvicorn) + `scripts/smoke_check.py` | Semua langkah sesuai harapan |
| `APP_ENV=production` | `/docs` & `/openapi.json` 404, `/health` 200 |
| Konfigurasi salah (`CORS_ORIGINS=*`, `SECRET_KEY` pendek) | App menolak start |
| Pemindaian Supabase | Tidak ada import/dependency/query; kata "Supabase" tersisa hanya di docstring, komentar, dan dokumen |
| Pengaman tes integrasi | DB bernama `postgres` ditolak |
| ZIP | Lihat bagian 12 |

**Bukti pemindaian ≠ bukti bebas Supabase di runtime.** Yang terbukti: kode aktif tidak memakai SDK/REST Supabase, dan seluruh alur API berjalan di PostgreSQL biasa (lokal). Tidak terbukti: perilaku terhadap server Supabase Anda (pooler, SSL, batas koneksi).

## 10. Penilaian
Skor numerik 0–100 **tidak diberikan**: bukti yang ada (satu lingkungan lokal, tanpa frontend, tanpa data nyata, tanpa beban) tidak cukup untuk angka yang jujur. Ringkasan kualitatif: modularitas & debuggability **kuat** (diuji otomatis), keamanan **layak untuk MVP** dengan celah di S10–S14, konsistensi database **baik** setelah 0003 (belum diuji di data nyata), kesiapan frontend **baik** dengan catatan tipe respons.

## 11. Pekerjaan tersisa & risiko
Prioritas sebelum dipakai publik: (1) uji ke database Supabase/produksi **setelah backup**; jalankan `stamp 0002` → tinjau → `upgrade head`; (2) rate limit terdistribusi bila >1 worker; (3) HTTPS + origin CORS produksi; (4) `response_model`; (5) strategi sesi (refresh/revoke) bila dibutuhkan; (6) ganti `passlib`/uji Python 3.13; (7) putuskan TIMESTAMPTZ; (8) perluas audit; (9) CI untuk `pytest` + tes integrasi.
Risiko migrasi 0003: berhenti bila ada email kembar; constraint `NOT VALID` tidak memeriksa data lama sampai `VALIDATE`; `NOT NULL` mengisi `role='user'`/`status='want_to_watch'` pada baris NULL lama.

## 12. Menjalankan proyek
Lihat `README.md`. Ringkas: `cp .env.example .env` → isi `DATABASE_URL` & `SECRET_KEY` → `alembic upgrade head` → `./run.sh` → `/docs`. Tes: `pytest -q`; integrasi: set `TEST_DATABASE_URL` ke database khusus tes.
