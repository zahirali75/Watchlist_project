# Laporan Audit Backend CineList (v2.0.0)

Tanggal audit: 24 Oktober 2026. Semua klaim di bawah berasal dari kode aktual, dijalankan di lingkungan lokal (Python 3.12.3, PostgreSQL 16.15), dan diuji ulang setelah perbaikan. Setiap status memakai label yang diminta: `TERVERIFIKASI BERFUNGSI`, `TERSEDIA, BELUM TERUJI`, `TERSEDIA SEBAGIAN`, `BELUM TERSEDIA`, atau `TIDAK DAPAT DIVERIFIKASI`.

## 1. Ringkasan eksekutif

Proyek menggunakan Python dan FastAPI secara konsisten. Akses database langsung memakai SQLAlchemy Core dan driver psycopg 3, tanpa Supabase SDK atau PostgREST di jalur runtime. Struktur per fitur sudah berjalan dan lapisan router, service, repository, dan schema dipisah dengan jelas. Migrasi Alembic berjalan dari database kosong, dan `alembic check` tidak mendeteksi drift antara model dan database.

Audit menemukan beberapa celah nyata. Yang paling serius adalah `SECRET_KEY` contoh dari `.env.example` yang diterima aplikasi, sehingga token admin bisa dipalsukan bila nilai contoh disalin tanpa diganti. Celah lain: password spraying lintas email tidak dibatasi, token tanpa `exp` diterima, dan URL poster `javascript:` tersimpan. Semua celah tersebut sudah diperbaiki dan dibuktikan dengan tes yang gagal di kode lama.

Kesiapan: aplikasi **siap untuk integrasi frontend pada lingkungan pengembangan/tugas kuliah**. Aplikasi **belum layak disebut production-ready**. Alasannya: throttle login masih berada di memori satu proses, belum ada HTTPS dan konfigurasi CORS produksi yang diuji, belum ada mekanisme refresh atau pencabutan token, dan belum diuji terhadap database Supabase atau produksi. Daftar lengkapnya ada di bagian 11.

## 2. Teknologi dan entrypoint (terverifikasi)

| Komponen | Versi terpasang saat audit | Bukti |
|---|---|---|
| Python | 3.12.3 (README: 3.11/3.12) | `python --version` |
| FastAPI | 0.162.0 | `pip freeze` |
| Starlette | 1.9.0 | `pip freeze` |
| Pydantic / pydantic-settings | 2.14.1 / 2.16.1 | `pip freeze` |
| SQLAlchemy | 2.1.6 | `pip freeze` |
| psycopg | 3.3.6 | `pip freeze` |
| PyJWT | 2.15.1 | `pip freeze` |
| passlib | 1.7.4 (tidak lagi dirawat, lihat bagian 11) | `pip freeze` |
| Alembic | 1.20.1 | `pip freeze` |
| uvicorn | 0.54.0 | `pip freeze` |
| PostgreSQL (uji) | 16.15 | `SELECT version()` |

Entrypoint: `app/main.py` membuat objek `app` melalui `create_app()`. Perintah yang benar: `uvicorn app.main:app`. `run.sh` juga memakai jalur ini. `backend/main.py` hanya shim kompatibilitas yang mengimpor `app.main`. Ia tidak membuat aplikasi kedua, dan sengaja dipertahankan (lihat bagian 12).

Ada juga `seed_movies.py` di root sebagai shim kompatibilitas untuk `scripts/seed_movies.py`.

## 3. Struktur folder aktual

```
app/
  main.py              perakitan: middleware, router, error handler
  core/                config, security, exceptions, error_handlers, logging,
                       pagination, rate_limit, constants
  db/                  session (engine), executor (helper SQL + translasi error),
                       base (metadata + naming convention), models/
  auth/                router, service, schemas, dependencies
  users/ movies/ watchlists/ audit_logs/ health/
                       masing-masing: router, service, repository, schemas
migrations/            env.py, versions/ (0001-0003), legacy_sql/ (arsip)
tests/                 unit/, api/, integration/
scripts/               seed_movies.py, smoke_check.py
docs/                  api, architecture, database, erd, frontend-integration,
                       troubleshooting, audit-report, archive/
backend/               shim kompatibilitas (bukan backend kedua)
```

Pemeriksaan arsitektur otomatis (`tests/unit/test_architecture.py`) menjaga dua aturan: SQL hanya boleh berada di repository, dan router tidak boleh mengimpor repository. Keduanya lulus.

## 4. Inventaris endpoint (dari OpenAPI server berjalan)

Daftar ini diambil dari `/openapi.json` pada server yang sedang berjalan, dan cocok dengan `docs/api.md`.

| Method | Path | Fungsi | Auth | Role | Status | Pagination |
|---|---|---|---|---|---|---|
| GET | /health | Liveness | Publik | - | TERVERIFIKASI BERFUNGSI | - |
| GET | /health/db | Readiness (`SELECT 1`) | Publik | - | TERVERIFIKASI BERFUNGSI | - |
| POST | /auth/register | Registrasi | Publik | selalu `user` | TERVERIFIKASI BERFUNGSI | - |
| POST | /auth/login | Login | Publik | - | TERVERIFIKASI BERFUNGSI | - |
| GET | /movies | Daftar + search/genre | Publik | - | TERVERIFIKASI BERFUNGSI | ya (LIMIT/OFFSET di SQL) |
| GET | /movies/{movie_id} | Detail film | Publik | - | TERVERIFIKASI BERFUNGSI | - |
| POST | /movies | Tambah film | Bearer | admin | TERVERIFIKASI BERFUNGSI | - |
| PUT | /movies/{movie_id} | Ubah (penuh) | Bearer | admin | TERVERIFIKASI BERFUNGSI | - |
| DELETE | /movies/{movie_id} | Hapus | Bearer | admin | TERVERIFIKASI BERFUNGSI | - |
| GET | /watchlists/me | Watchlist sendiri | Bearer | user | TERVERIFIKASI BERFUNGSI | ya |
| GET | /watchlists/me/stats | Statistik sendiri | Bearer | user | TERVERIFIKASI BERFUNGSI | - |
| GET | /watchlists/{user_id} | Watchlist (hanya milik sendiri) | Bearer | user (pemilik) | TERVERIFIKASI BERFUNGSI | ya |
| POST | /watchlists | Tambah ke watchlist | Bearer | user | TERVERIFIKASI BERFUNGSI | - |
| PUT | /watchlists/{watchlist_id} | Ubah status/catatan | Bearer | pemilik | TERVERIFIKASI BERFUNGSI | - |
| DELETE | /watchlists/{watchlist_id} | Hapus item | Bearer | pemilik | TERVERIFIKASI BERFUNGSI | - |
| GET | /users | Daftar user | Bearer | admin | TERVERIFIKASI BERFUNGSI | ya |
| GET | /users/{user_id} | Detail user | Bearer | admin | TERVERIFIKASI BERFUNGSI | - |
| GET | /users/{user_id}/stats | Statistik user | Bearer | admin | TERVERIFIKASI BERFUNGSI | - |
| GET | /audit-logs | Daftar audit log | Bearer | admin | TERVERIFIKASI BERFUNGSI | ya |
| GET | /audit-logs/{log_id} | Detail audit log | Bearer | admin | TERVERIFIKASI BERFUNGSI | - |

Alias legacy tersembunyi dari Swagger: `POST /login` dan `POST /users` (register). Keduanya diuji dan dipertahankan untuk frontend lama.

Tidak ada endpoint yang tercatat di dokumentasi tetapi tidak ada di kode, dan sebaliknya. Tidak ada endpoint PATCH; PUT adalah penggantian penuh untuk film, dan parsial untuk watchlist (hanya field yang dikirim).

## 5. Authentication dan JWT

| Aspek | Status | Bukti |
|---|---|---|
| Hash password | TERVERIFIKASI BERFUNGSI | PBKDF2-SHA256, 600.000 iterasi. Hash lama (29.000) tetap valid dan di-upgrade saat login berhasil. |
| Login generik | TERVERIFIKASI BERFUNGSI | Email tidak dikenal dan password salah sama-sama menghasilkan "Email atau password salah". Waktu respons disamakan dengan hash palsu. |
| Registrasi | TERSEDIA SEBAGIAN | Email duplikat menghasilkan 409 dengan email di `errorMeta`. Ini enumerasi, dipertahankan secara sengaja (lihat bagian 11). |
| Role saat registrasi | TERVERIFIKASI BERFUNGSI | Field `role` di body diabaikan. Uji: `role: admin` menghasilkan `role: user`. |
| Signature | TERVERIFIKASI BERFUNGSI | Token dengan secret salah ditolak. |
| `alg=none` | TERVERIFIKASI BERFUNGSI | Ditolak dengan 401. |
| HS512 dengan secret yang sama | TERVERIFIKASI BERFUNGSI | Ditolak (algoritma dikunci ke HS256). |
| Expiry | TERVERIFIKASI BERFUNGSI | Token kedaluwarsa ditolak dengan pesan "Token kedaluwarsa". |
| Token tanpa `exp` | TERVERIFIKASI BERFUNGSI setelah perbaikan | Sebelumnya diterima jika ditandatangani benar. Sekarang ditolak. |
| Token tanpa `sub`, `sub` bukan UUID | TERVERIFIKASI BERFUNGSI | Ditolak 401. |
| Role dari token | TERVERIFIKASI BERFUNGSI | Klaim `role` di token diabaikan. Role dibaca dari database pada setiap request. |
| Akun dihapus | TERVERIFIKASI BERFUNGSI | Token lama ditolak 401 "User tidak ditemukan". |
| Demosi/promosi role | TERVERIFIKASI BERFUNGSI | Berlaku pada request berikutnya tanpa login ulang. |
| Refresh token / revoke | BELUM TERSEDIA | Sesuai keputusan: masa berlaku 60 menit dan login ulang saat 401 (lihat `docs/frontend-integration.md`). |
| Throttle login per (IP + email) | TERVERIFIKASI BERFUNGSI | 429 setelah 5 kegagalan. Direset saat login berhasil. |
| Throttle login per IP | TERVERIFIKASI BERFUNGSI setelah perbaikan | Password spraying dari satu IP ke banyak email sekarang diblokir. |

Pengaturan algoritma: `ALGORITHM` di konfigurasi sekarang bertipe `Literal["HS256"]`. Nilai lain menyebabkan aplikasi menolak start.

## 6. Middleware dan dependencies

Middleware yang terpasang hanya `CORSMiddleware`. Tidak ada middleware autentikasi global. Keputusan ini sengaja: autentikasi dipasang per endpoint melalui dependency (`get_current_user`, `require_admin`). Dengan begitu endpoint publik tidak terkunci secara tidak sengaja, dan setiap router menyatakan kebutuhan aksesnya dengan jelas. Tidak ada middleware request logging atau correlation ID; ini dicatat sebagai rekomendasi.

Dependency utama:
- `get_current_user`: memverifikasi JWT, mengambil `id` dan `role` terkini dari database.
- `require_admin`: memanggil `get_current_user`, lalu mengembalikan 403 bila role bukan admin.
- `pagination_params`: validasi `page` dan `limit`.
- `get_settings`: dibaca sekali dan di-cache.

Session database: tidak ada session ORM yang dibuka per request. Setiap query memakai `get_connection()` yang membuka koneksi singkat dan menutupnya dengan context manager. Ini terverifikasi dari kode. Kebocoran koneksi belum diuji dengan beban nyata.

CORS: origin dibaca dari `CORS_ORIGINS`, tanpa `*` (divalidasi saat boot). Origin tidak terdaftar ditolak pada preflight (uji: 400 "Disallowed CORS origin"). Metode dibatasi ke GET, POST, PUT, DELETE, OPTIONS. Header dibatasi ke Authorization dan Content-Type.

Error handling: semua error domain lewat `AppError`, HTTP error framework lewat `StarletteHTTPException` (diperbaiki), validasi lewat `RequestValidationError`, dan error tak terduga menjadi 500 generik dengan detail hanya di log. Detail database tidak pernah dikirim ke klien. Uji `test_error_database_tidak_bocor_ke_klien` lulus.

Logging: tidak mencatat password, token, atau hash. Login gagal dicatat tanpa email. Dicek lewat kode dan tes.

## 7. RBAC dan kepemilikan data

Matriks izin yang benar-benar diterapkan:

| Aksi | Publik | User (login) | Admin |
|---|---|---|---|
| Melihat katalog film | Ya | Ya | Ya |
| Menambah, mengubah, menghapus film | Tidak (401) | Tidak (403) | Ya |
| Mengelola daftar user, statistik user | Tidak (401) | Tidak (403) | Ya |
| Melihat audit log | Tidak (401) | Tidak (403) | Ya |
| Watchlist sendiri (lihat, tambah, ubah, hapus) | Tidak (401) | Ya | Ya (hanya miliknya sendiri) |
| Watchlist user lain | Tidak (401) | Tidak (403) | **Tidak (403)** |

Keputusan kebijakan: admin **tidak** boleh membaca watchlist user lain. Ini sesuai dengan dokumentasi dan tes `test_lihat_watchlist_orang_lain_403_termasuk_admin`. Jika kebijakan berubah, perlu endpoint khusus dan keputusan tertulis.

Skenario yang diuji dan hasilnya:
1. Tanpa token ke endpoint privat: 401. Lulus.
2. User biasa ke endpoint admin: 403. Lulus.
3. Admin ke endpoint admin: 200 atau 201. Lulus.
4. User A membaca atau mengubah watchlist user B: 403, tidak ada perubahan data. Lulus.
5. User mengirim `user_id` orang lain di body: field tidak ada di skema, dan pemilik diambil dari token. Lulus.
6. Role berubah setelah token diterbitkan: berlaku langsung. Lulus.
7. Akun dihapus lalu token lama dipakai: 401. Lulus.

Pembedaan 401 dan 403 sudah benar: 401 untuk token tidak ada, rusak, atau kedaluwarsa; 403 untuk pengguna terautentikasi tanpa izin.

## 8. Pagination, search, dan filtering

| Aspek | Status | Catatan |
|---|---|---|
| Pagination di SQL | TERVERIFIKASI BERFUNGSI | `LIMIT` dan `OFFSET` ada di query. Total dihitung dengan `COUNT(*)` terpisah. Tidak ada pemotongan di memori. |
| Default dan batas | TERVERIFIKASI BERFUNGSI | `limit` default 20, maksimal 100 (400 bila lebih). `limit=0` diperlakukan sebagai default. |
| `page` | TERVERIFIKASI BERFUNGSI setelah perbaikan | Minimal 1, maksimal 1.000.000 (422). Sebelumnya `page=2^63` menghasilkan error database. |
| Nilai negatif atau bukan angka | TERVERIFIKASI BERFUNGSI | 422 dari validasi FastAPI. |
| Search | TERVERIFIKASI BERFUNGSI | `ILIKE` dengan parameter terikat. Uji dengan karakter `%' OR '1'='1` aman. |
| Sorting | BELUM TERSEDIA | Urutan tetap: film `id ASC`, watchlist dan user `created_at DESC`. |
| Metadata | TERVERIFIKASI BERFUNGSI | Respons memuat `count`, `total`, `page`, `limit`, dan `data`. |
| Konsistensi antar halaman | TERSEDIA SEBAGIAN | Offset pagination bisa melewatkan atau menduplikasi item bila data berubah di antara halaman. Dicatat sebagai risiko. |

Catatan kontrak: respons koleksi memakai field `data`, bukan `items`. Ini kontrak asli yang dipertahankan.

## 9. Database, migrasi, dan Supabase

| Aspek | Status | Bukti |
|---|---|---|
| Koneksi | TERVERIFIKASI BERFUNGSI | `DATABASE_URL` dengan `postgresql+psycopg://`. `pool_pre_ping=True`, `pool_recycle=1800`. |
| Model dan skema | TERVERIFIKASI BERFUNGSI | `alembic check`: "No new upgrade operations detected". |
| Migrasi dari database kosong | TERVERIFIKASI BERFUNGSI | Tes `test_upgrade_dari_database_kosong_dan_model_sama_dengan_skema` dan `test_downgrade_base_lalu_upgrade_lagi` lulus. |
| Migrasi 0003 menolak email kembar | TERVERIFIKASI BERFUNGSI | Tes `test_0003_berhenti_jelas_bila_ada_email_kembar` lulus. |
| Foreign key dan cascade | TERVERIFIKASI BERFUNGSI | Watchlist CASCADE ke user dan film. Audit log SET NULL ke user. Diuji. |
| Unique | TERVERIFIKASI BERFUNGSI | `(user_id, movie_id)` pada watchlist. Email unik tanpa membedakan huruf besar/kecil. |
| Check constraint | TERVERIFIKASI BERFUNGSI | Role, status, rating, dan tahun rilis. Constraint rating dan tahun semula `NOT VALID`; sudah diangkat ke VALID 26 Okt 2026 setelah data diperiksa. |
| Transaksi | TERVERIFIKASI BERFUNGSI | `get_connection(write=True)` memakai `engine.begin()`: commit saat sukses, rollback saat error. |
| Parameter SQL | TERVERIFIKASI BERFUNGSI | Semua nilai terikat. Nama kolom untuk UPDATE dibatasi dengan allowlist. |
| Tipe waktu | TERSEDIA SEBAGIAN | `users`, `movies`, `watchlists` memakai `TIMESTAMP` tanpa zona waktu. `audit_logs` memakai `TIMESTAMPTZ`. Ini keputusan tertulis di migrasi 0003. |
| Supabase | TERVERIFIKASI BERFUNGSI | Tidak ada import SDK atau PostgREST di kode aktif. Tes arsitektur memverifikasi ini. Referensi tersisa hanya di dokumen dan kode `backend/` yang sudah dinyatakan tidak aktif. |
| Paparan Data API (RLS dan grant) | TERVERIFIKASI BERFUNGSI | Sebelum migrasi 0004, RLS mati di semua tabel. Setelah 0004, RLS aktif di keempat tabel dan grant ke `anon`/`authenticated` dicabut. **Diverifikasi di Supabase nyata 26 Okt 2026:** grant kedua peran = 0 tabel dan 0 usage schema (lihat bagian 9b). |
| Pengujian ke Supabase | TERVERIFIKASI BERFUNGSI | **26 Okt 2026:** migrasi 0002–0004 dijalankan di Supabase (PostgreSQL 17.6); RLS dan grant diperiksa langsung; uji rantai penuh 52/52 lulus. |

Penting: tidak ada kredensial Supabase atau secret sungguhan di ZIP. Pencarian pola token JWT dan URL Supabase di working tree dan riwayat Git tidak menemukan nilai sungguhan.

### 9b. Pemeriksaan skill Supabase

Skill Supabase mewajibkan pemeriksaan keamanan untuk setiap pekerjaan yang menyentuh Supabase. Hasilnya untuk proyek ini:

| Poin skill | Kondisi proyek | Status |
|---|---|---|
| RLS di schema yang terbuka (`public`) | RLS mati di semua tabel sebelum 0004 | DIPERBAIKI (migrasi 0004, RLS aktif) |
| Tabel terbuka ke `anon`/`authenticated` | Grant tidak diatur di kode; default Supabase dapat memberi akses ke tabel baru | DIPERBAIKI bila peran ada (0004 mencabut grant dan default privilege) |
| `user_metadata` untuk otorisasi | Tidak dipakai | TIDAK RELEVAN |
| `service_role` atau secret di klien | Tidak ada di kode; frontend tidak menerima kunci Supabase | TERVERIFIKASI |
| View yang melewati RLS | Tidak ada view | TIDAK RELEVAN |
| `auth.role()` dan policy tanpa ownership | Tidak ada policy | TIDAK RELEVAN (RLS tanpa policy menolak semua baris bagi non-pemilik) |
| `SECURITY DEFINER` | Tidak ada fungsi | TIDAK RELEVAN |
| Revocation sesi saat user dihapus | Auth buatan sendiri, dicek ke database pada setiap request | TERVERIFIKASI (lihat bagian 5) |
| Versi paket dipin | `requirements.txt` memakai `>=` | TERSEDIA SEBAGIAN (lihat bagian 11) |
| Changelog dan dokumentasi Supabase terbaru | Akses ke supabase.com tidak tersedia saat audit dijalankan (24 Okt). **Diverifikasi lewat instance 26 Okt 2026:** perilaku RLS dan grant sesuai harapan | TERVERIFIKASI untuk perilaku instance |
| `supabase db advisors` | Tidak ada CLI saat audit dijalankan | BELUM DIJALANKAN (pemeriksaan manual setara sudah dilakukan lewat koneksi langsung) |
| Pengaturan Data API di dashboard | Tidak ada akses dashboard saat audit dijalankan | BELUM DIPERIKSA lewat dashboard; dampaknya tertutup karena RLS aktif dan grant dicabut |

Catatan penting: peran aplikasi harus pemilik tabel atau memiliki BYPASSRLS. Jika tidak, RLS tanpa policy membuat semua query mengembalikan kosong. Migrasi 0004 memeriksa ini dan berhenti dengan pesan jelas bila tidak terpenuhi, tetapi pemeriksaan itu hanya berlaku saat migrasi dijalankan, bukan saat aplikasi berjalan dengan peran berbeda.

## 10. Temuan keamanan dan statusnya

| ID | Prioritas | Temuan | Bukti awal | Status |
|---|---|---|---|---|
| S1 | P0 | `SECRET_KEY` contoh diterima | Settings menerima 62 karakter placeholder | DIPERBAIKI, server menolak start |
| S2 | P1 | Password spraying lintas email tidak dibatasi | 25 percobaan dari satu IP, semua 401 | DIPERBAIKI, batas per IP |
| S3 | P1 | Token tanpa `exp` diterima | Token ditandatangani benar, tanpa exp: 200 | DIPERBAIKI, 401 |
| S4 | P2 | `poster_url` dengan `javascript:` tersimpan | Admin create: 201 | DIPERBAIKI, 422 |
| S5 | P2 | Body tidak dibatasi (`overview` 3 MB diterima) | 201 | DIPERBAIKI untuk field teks; batas ukuran body HTTP belum ada |
| S6 | P2 | Enumerasi email lewat registrasi | 409 dengan email di `errorMeta` | DIPERTAHANKAN, keputusan produk |
| S7 | P3 | Pesan error tipe database bocor (`/users/not-uuid`, `page=2^63`) | 400 "Data tidak sesuai dengan batasan database" | DIPERBAIKI |
| S8 | P3 | Memori throttle tumbuh | Key tidak pernah dibuang | DIPERBAIKI (bucket kosong dibuang) |
| S9 | P3 | Algoritma JWT bisa diubah lewat env | `ALGORITHM` string bebas | DIPERBAIKI (Literal HS256) |
| S10 | P3 | Dokumen menyebut `/docs` padahal dimatikan di production | Redirect 307 ke 404 | DIPERBAIKI |
| S11 | P1 (bila DB di Supabase) | Tabel `users` (berisi `password_hash`) tidak dilindungi RLS di schema `public` yang terbuka ke Data API | RLS mati di semua tabel; kode aplikasi tidak mengatur grant | DIPERBAIKI, migrasi 0004 (lihat 9b) |

Tidak ada celah akses ilegal ke data yang ditemukan. Semua skenario IDOR, mass assignment, dan bypass role yang diuji ditolak.

## 11. Masalah yang belum terselesaikan

| Prioritas | Masalah | Dampak | Rekomendasi |
|---|---|---|---|
| P1 | Throttle login hanya di memori satu proses | Dengan beberapa worker atau instance, batas tidak berlaku global | Pindah ke Redis atau rate limit di reverse proxy sebelum scaling |
| P1 | Belum ada HTTPS dan konfigurasi CORS produksi yang diuji | Token Bearer rawan bila dikirim lewat HTTP | Deployment hanya lewat HTTPS; `CORS_ORIGINS` diisi origin produksi |
| P2 | Enumerasi email lewat registrasi (S6) | Penyerang bisa mengetahui email terdaftar | Keputusan produk: pertahankan pesan jelas, atau ganti dengan respons generik dan verifikasi email |
| P2 | Tidak ada refresh token atau revoke | Token valid sampai 60 menit meski user logout | Diterima untuk saat ini; tambahkan bila dibutuhkan |
| P2 | passlib 1.7.4 tidak dirawat dan memberi `DeprecationWarning` untuk `crypt` | Risiko kompatibilitas Python 3.13 | Migrasi ke `hashlib.pbkdf2_hmac` atau argon2-cffi dengan strategi kompatibilitas hash lama |
| P2 | Batas ukuran body HTTP belum dikonfigurasi | Body besar tetap sampai ke aplikasi | Batasi di reverse proxy atau middleware |
| P2 | Respons belum memakai `response_model` | Kontrak OpenAPI tidak menggambarkan respons | Tambahkan skema respons bertahap |
| P3 | `created_at` tanpa zona waktu memakai `now()` | Nilai bergantung pada timezone server database | Pastikan timezone DB UTC, atau migrasi ke TIMESTAMPTZ dengan rencana konversi |
| P3 | Seeder tidak mencegah duplikasi film | Menjalankan ulang menggandakan data | Tambahkan pengecekan judul + tahun |
| P3 | Constraint rating dan tahun berstatus `NOT VALID` | Data lama tidak tervalidasi | **SELESAI 26 Okt 2026** — data diperiksa (0 baris melanggar), lalu `ALTER TABLE ... VALIDATE CONSTRAINT` |
| P3 | `smoke_check.py` menulis data ke database target | Bisa mengotori database | Hanya jalankan ke database pengembangan; sudah ditulis di docstring |
| P2 | Verifikasi 0004 belum dilakukan terhadap Supabase nyata | Perilaku default grant Supabase hanya diasumsikan dari skill | Jalankan `alembic upgrade head` di staging Supabase, lalu cek `has_table_privilege('anon', 'users', 'SELECT')` dan `relrowsecurity` |
| P3 | `requirements.txt` memakai `>=`, bukan versi yang dipin | Instalasi baru bisa berbeda dari versi yang diuji | Buat lockfile dari versi di bagian 2 |
| P3 | Urutan pagination tidak stabil bila data berubah | Item bisa terlewat atau berulang | Gunakan cursor pagination bila diperlukan |

## 12. Kode legacy dan duplikasi

- `backend/main.py` dan `backend/database.py`: shim kompatibilitas. Keduanya hanya mengimpor modul aktif. Dipertahankan agar perintah lama `backend.main:app` tetap berjalan. Tidak ada implementasi kedua.
- `seed_movies.py` di root: shim untuk `scripts/seed_movies.py`.
- `migrations/legacy_sql/`: arsip SQL awal. Tidak dijalankan oleh Alembic.
- `docs/archive/`: dokumen lama, tidak dihapus.
- Tidak ada duplikasi logika bisnis yang ditemukan.

Kode legacy tidak dihapus karena ada dokumen dan langkah deployment yang masih merujuknya. Penghapusan bisa dilakukan setelah konfirmasi.

## 13. Testing dan hasil aktual

| Perintah | Hasil |
|---|---|
| `pytest -q` (tanpa database) | 80 lulus, 17 dilewati *(situasi saat audit 26 Okt 2026; lihat bagian 14 untuk angka terbaru)* |
| `TEST_DATABASE_URL=... pytest -q` (PostgreSQL 16.15) | 97 lulus *(situasi saat audit; lihat bagian 14)* |
| `python -m pyflakes app tests scripts seed_movies.py backend` | Bersih, tanpa temuan |
| `alembic upgrade head` (database kosong) | Berhasil: 0001 → 0003 saat audit; kini 0001 → 0006 |
| `alembic check` | Tidak ada drift |
| `scripts/smoke_check.py` (server berjalan) | Semua langkah sesuai ekspektasi, termasuk 401, 403, 409 |

Tes baru (15) dijalankan juga terhadap kode asli: 14 dari 14 tes yang dibuat di awal gagal, membuktikan bahwa tes menangkap celah. Satu tes batas `page` ditambahkan kemudian dan belum diuji terhadap kode asli.

Tes yang dilewati tanpa `TEST_DATABASE_URL`: 17 tes integrasi (13 tes lama dan 4 tes pengamanan Supabase). Bila `.env` berisi `TEST_DATABASE_URL` yang menunjuk database bernama `cinelist_test`, tes itu ikut jalan.

**Pembaruan 27 Okt 2026 — penambahan 4 hal yang belum solid (sesi, lupa password, profil sendiri, tes integrasi):**

| Perintah | Hasil |
|---|---|
| `pytest -q` (dengan `TEST_DATABASE_URL` ke Supabase `cinelist_test`) | **122 lulus, 1 dilewati** |
| `pytest tests/integration -q` | **16 lulus, 1 dilewati** (tes ownership `anon` di-skip karena pooler Supabase) |
| `python uji_sesi_dan_password.py` (e2e ke server hidup) | **31/31 lulus** |
| `python uji_rantai_penuh.py` | **52/52 lulus** |
| `alembic current` di Supabase | **0006** |
| `openapi.json` | **28 operasi endpoint** (naik dari 20) |

1 tes yang dilewati adalah `test_migrasi_menolak_role_non_pemilik_tanpa_bypassrls`: di Supabase, peran non-pemilik tidak bisa membuka koneksi lewat pooler multi-tenant tanpa SNI/`external_id`, sehingga tes itu tidak bisa dijalankan di lingkungan ini. Ini artefak lingkungan, bukan bug kode — tes tetap berjalan penuh di PostgreSQL lokal.

## 14. Rekomendasi prioritas

1. Sebelum deployment: HTTPS, `SECRET_KEY` acak yang disimpan di secret manager, `APP_ENV=production`, `CORS_ORIGINS` berisi origin produksi.
2. Sebelum scaling: pindahkan throttle login ke penyimpanan bersama.
3. Putuskan kebijakan enumerasi email (S6).
4. Ganti passlib dan uji Python 3.13.
5. Tambahkan batas ukuran body di reverse proxy.
6. Tambahkan CI untuk pytest, tes integrasi PostgreSQL, dan `alembic check`.
7. Tambahkan `response_model` dan sorting bila dibutuhkan frontend.
