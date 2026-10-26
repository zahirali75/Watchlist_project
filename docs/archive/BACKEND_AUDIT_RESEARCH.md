# Riset dan audit backend CineList

Tanggal audit: 24 Oktober 2026  
Objek: arsip `Watchlist_project_rapi(1).zip` yang disediakan pada percakapan ini.

## Ringkasan eksekutif

CineList sudah memiliki fondasi API yang layak untuk **MVP/kebutuhan proyek kuliah**: registrasi/login, JWT access token, role `user`/`admin`, katalog film, watchlist per pengguna, validasi Pydantic, pagination, error handler, dan audit log. Akan tetapi, belum tepat dinyatakan siap produksi. Ketidakcocokan dokumentasi ERD, integritas skema, kontrol autentikasi, pencatatan audit, test integrasi, dan migrasi database masih perlu dibereskan.

Audit menemukan kebutuhan tambahan yang dinyatakan di percakapan: **query backend tidak boleh bergantung pada Supabase SDK/PostgREST**. Pada versi hasil audit ini, seluruh jalur runtime, termasuk compatibility import lama di `backend/` dan kedua seeder, diarahkan ke PostgreSQL langsung melalui SQLAlchemy Core/psycopg. Modul `backend/main.py` kini alias menuju aplikasi aktif, dan `backend/database.py` hanya mengekspor koneksi PostgreSQL. Pemindaian kode executable tidak lagi menemukan query Supabase/PostgREST.

## Kebutuhan fungsional yang disimpulkan dari project

| Kebutuhan | Status | Catatan |
|---|---|---|
| Registrasi dan login | Sebagian besar ada | Hash password dan JWT sudah tersedia; throttling login, verifikasi email, reset password, dan pencabutan token belum ada. Untuk MVP beberapa fitur tambahan itu bisa ditunda. |
| Katalog film | Ada | Daftar, detail, pencarian, filter genre, pagination; CRUD dibatasi untuk admin. |
| Watchlist pribadi | Ada | Tambah, lihat, ubah status/catatan, hapus, statistik; ownership diperiksa di service. |
| Role user/admin | Ada | Role disimpan di `users.role` dan dikirim di JWT; tidak ada UI/API promosi admin yang terkendali, sehingga perlu prosedur operasi terdokumentasi. |
| Audit log | Sebagian | Registrasi serta perubahan katalog film dicatat; login gagal dan perubahan watchlist belum dicatat. Kegagalan audit sengaja tidak menggagalkan operasi utama. |
| Database tidak bergantung pada Supabase API | Diterapkan pada source executable | Repository memakai SQL berparameter lewat SQLAlchemy Core; `backend/` sekarang compatibility shim, bukan implementasi kedua. |
| Migrasi skema berulang/reproducible | Belum | SQL manual tersedia, namun Alembic belum memiliki revision aktif dan `target_metadata` masih `None`. |
| Tes otomatis | Belum terbukti lulus di lingkungan audit | Tes memakai mocks; eksekusi tidak dapat dimulai karena `passlib` tidak terpasang dan instalasi tidak dapat dilakukan karena jaringan paket tidak tersedia. Kompilasi sintaks Python lulus. |
| Integrasi frontend | Tidak dapat dinilai penuh | Frontend tidak disertakan; kontrak respons dan endpoint harus dicocokkan lagi dengan implementasi frontend sebenarnya. |

## Arsitektur dan database

### Yang sudah baik

- Pemisahan `routers`, `schemas`, `services`, `repositories`, dan `core` membuat tanggung jawab relatif jelas.
- `app/main.py` menjadi satu entry point aktif dan memasang CORS serta exception handler terpusat. `backend.main:app` hanya alias ke app yang sama, agar tidak ada jalur duplikat yang berbeda konfigurasi.
- Query SQL menggunakan parameter bernama, bukan menggabungkan nilai masukan ke SQL secara langsung. Nama kolom dinamis pada UPDATE dibatasi melalui allowlist.
- `watchlists` mempunyai foreign key ke `users` dan `movies`, serta unique constraint `(user_id, movie_id)` untuk mencegah duplikasi.
- Penghapusan watchlist difokuskan ke pemiliknya. Endpoint pengelolaan film, users, dan audit log membatasi operasi sesuai role.

### Temuan yang harus ditindaklanjuti

1. **ERD lama tidak merepresentasikan skema aktif.** Dokumen sebelumnya memasukkan `reviews`, `favorites`, `collections`, `collection_movies`, `bio`, dan `avatar_url`, serta menyebut ID user integer. DDL aktif menggunakan `users.id UUID`, `watchlists.user_id UUID`, dan hanya empat tabel aktif (`users`, `movies`, `watchlists`, `audit_logs`, dengan tabel audit memerlukan migration 0002). Dokumentasi ERD telah diperbarui di `backend/database_schema.md`.
2. **`schema.sql` tidak membuat `audit_logs`.** Database baru memerlukan DDL dasar (`schema.sql` atau migrasi 0001) ditambah migrasi `0002_audit_logs.sql`.
3. **Constraint belum menegakkan seluruh aturan bisnis.** `users.role` dan `watchlists.status` memiliki `DEFAULT` dan `CHECK`, tetapi belum `NOT NULL`; database masih dapat menerima NULL. `movies.rating` belum dibatasi oleh CHECK 0–10, dan `release_year` belum dibatasi oleh invariant yang sama dengan validasi API.
4. **Tipe timestamp bercampur.** Tiga tabel menggunakan `TIMESTAMP`, sedangkan `audit_logs.created_at` memakai `TIMESTAMPTZ`. Sebaiknya distandardisasi dengan migrasi yang memperhatikan data existing.
5. **`updated_at` perlu konsisten.** Kode API aktif sekarang memperbarui `watchlists.updated_at` ketika mengubah item. Perubahan yang dilakukan di luar API tetap tidak memperbarui kolom tersebut; trigger PostgreSQL dapat dipertimbangkan jika dibutuhkan.
6. **Pencarian katalog mungkin memerlukan indeks lain saat skala membesar.** B-tree pada `movies.title` tidak ideal untuk pola `ILIKE '%teks%'`; pertimbangkan `pg_trgm`/GIN setelah volume data membenarkan kompleksitasnya.
7. **Email case-insensitive belum dijamin constraint database.** Repository mencari email dengan `lower(email)` dan menyimpan email baru dalam huruf kecil, tetapi UNIQUE biasa pada `email` tidak menjamin keunikan untuk seluruh baris legacy dengan variasi kapitalisasi. Periksa data, lalu pertimbangkan unique index `lower(email)` dalam migrasi.
8. **Alembic belum siap untuk autogenerate.** Folder `alembic/versions/` belum memiliki revision dan `target_metadata` masih `None`. Saat ini prosedur yang terdokumentasi adalah migrasi SQL manual; jangan menganggap `alembic upgrade head` sudah mengelola skema proyek.

## Autentikasi, JWT, dan role

### Sudah diterapkan

- Token berisi `sub`, `role`, `iat`, dan `exp`; signature dan waktu kedaluwarsa diverifikasi.
- `SECRET_KEY` wajib dikonfigurasi dan panjang minimalnya 32 karakter.
- Endpoint terlindungi memakai dependency FastAPI `get_current_user`/`require_admin`; ini pola yang valid. Middleware JWT global bukan syarat wajib jika semua endpoint privat memanggil dependency yang benar.
- Registrasi menetapkan role `user`; user tidak dapat memilih role dari request publik.
- Password tidak disimpan dalam plain text.

### Gap keamanan

1. `get_current_user()` mengambil role dari JWT tanpa membaca status/role terkini di database. Jika role admin dicabut, token admin lama masih dapat berfungsi sampai `exp`. Pilih strategi sesuai kebutuhan: cek status/role ke database, token version, atau revocation list.
2. Belum ada rate limit untuk registrasi/login. Untuk deployment publik, batasi berdasarkan IP dan identitas/akun serta catat kegagalan login.
3. Belum ada refresh-token atau revocation/logout yang membatalkan access token sebelum expiry. Untuk MVP access token 60 menit bisa diterima bila risikonya terdokumentasi; untuk produksi perlu kebijakan sesi.
4. Hashing awal menggunakan Passlib PBKDF2 dengan default rounds yang secara historis 29.000. Ini jauh di bawah rekomendasi OWASP saat ini untuk PBKDF2-HMAC-SHA256 (600.000 rounds pada panduan password storage). Implementasi aktif telah diubah untuk membuat hash baru dengan 600.000 rounds dan meningkatkan hash lama pada login berhasil. Keberhasilan migrasi hash tetap memerlukan test runtime.
5. Versi historis `backend/main.py` pernah memiliki fallback `SECRET_KEY = "supersecretkey"` dan asumsi ID integer, sedangkan skema aktif menggunakan UUID. Risiko itu dihilangkan dari working tree: `backend/main.py` sekarang hanya alias ke aplikasi aktif dan tidak memiliki konfigurasi atau endpoint duplikat.
6. Belum ada flow untuk membuat/mempromosikan admin yang terdokumentasi. Tetapkan prosedur operator tepercaya; jangan pernah menerima `role=admin` dari register publik.

## Validasi dan kontrak API

- `RegisterUser` memvalidasi email dan minimum password 8 karakter; schema film memvalidasi title, tahun, rating, dan sebagian field; status watchlist dibatasi enum.
- Filter serta pagination mempunyai parameter yang tervalidasi, tetapi panjang parameter pencarian/catatan/deskripsi belum dibatasi secara konsisten.
- `MovieUpdate` adalah full replacement melalui PUT, bukan PATCH. Ini bisa benar jika disengaja, tetapi frontend harus mengetahui kontraknya.
- Schema response (`MovieRead`, `WatchlistRead`, `TokenResponse`) didefinisikan tetapi tidak dipakai secara konsisten sebagai `response_model`. Gunakan response models untuk kontrak OpenAPI yang stabil dan memastikan field sensitif tidak bocor.
- `GET /users/{user_id}/stats` dapat mengembalikan statistik nol untuk user yang tidak ada, karena service hanya menghitung watchlist dan tidak memverifikasi user; selaraskan dengan semantik endpoint user lain bila perlu.
- `WatchlistUpdate` memakai `exclude_none=True`, sehingga klien tidak dapat dengan jelas menghapus isi `notes` dengan mengirim `null`; putuskan apakah ini perilaku yang dikehendaki.

## Logging dan error handling

- Handler error global mengirim pesan generik untuk exception yang tidak ditangani.
- Query helper baru tidak mengembalikan pesan database mentah kepada klien.
- Audit log hanya mencakup beberapa event; tentukan event yang benar-benar penting (kegagalan login, akses admin, perubahan watchlist, perubahan privilege) dan kebijakan saat penulisan audit gagal. Jika audit adalah bukti kepatuhan, jangan menelan kegagalannya untuk seluruh operasi kritis.
- `GET /health` saat ini memeriksa aplikasi/config, bukan konektivitas database; bila dipakai untuk deployment, tambahkan endpoint readiness yang aman untuk memeriksa `SELECT 1`.

## Infrastruktur, middleware, dan deployment

- CORS terpasang dan origin diambil dari konfigurasi. Untuk produksi, atur origin hanya ke domain frontend sesungguhnya dan batasi metode/header ke yang dipakai.
- Belum ada rate limiting, security headers, atau trusted-host middleware yang dikonfigurasi oleh aplikasi. HTTPS sebaiknya diwajibkan di reverse proxy/platform; pertimbangkan `TrustedHostMiddleware` bila aplikasi menerima Host dari jaringan yang tidak dipercaya.
- `.env.example` kini menggunakan `DATABASE_URL` PostgreSQL langsung. Gunakan akun database khusus aplikasi dengan privilege minimum, bukan akun owner/superuser. Simpan kredensial di secret store dan jangan log DSN.
- File `scripts/smoke_check.py` menulis data uji ke API dan tetap mengasumsikan server pada port 8010. Jangan arahkan ke database produksi.

## Perubahan yang dilakukan pada salinan audit ini

- Repository aktif dipindahkan dari Supabase SDK/PostgREST ke query SQLAlchemy Core berparameter.
- Koneksi PostgreSQL langsung disediakan oleh `app/db/session.py` melalui `DATABASE_URL`.
- Seeder di `scripts/seed_movies.py` dan `seed_movies.py` menggunakan PostgreSQL langsung.
- `requirements.txt`, `.env.example`, config, fixture/config test, dokumen setup, migrasi manual, dan ERD diperbarui.
- Hash password baru memakai 600.000 rounds PBKDF2-HMAC-SHA256; hash lama ditingkatkan setelah login berhasil jika perlu.
- Error database generik tidak lagi mengirim `dbMessage` ke klien.
- Modul `backend/` sekarang menjadi compatibility shim yang mengekspor aplikasi/koneksi PostgreSQL aktif; query Supabase historis tidak lagi ada pada working tree dan versi yang lebih lama tetap tersedia dalam riwayat Git jika dibutuhkan untuk penelusuran.

## Hasil verifikasi

- **Kompilasi sintaks Python:** lulus (`compileall`).
- **Pemindaian statis:** tidak menemukan import/query Supabase atau PostgREST pada source runtime (`app/`, `backend/`, `scripts/`, seeder root, tests), dependencies aktif, atau `.env.example`. Sebutan Supabase pada dokumentasi hanya menjelaskan bahwa dependensi tersebut telah dihilangkan.
- **Unit/API tests:** belum dapat dijalankan. Proses `pytest` berhenti saat import `passlib` karena paket tidak terpasang. Upaya instalasi paket gagal karena lingkungan tidak mempunyai akses jaringan ke package index.
- **Integrasi PostgreSQL:** belum diuji, karena tidak ada DB test yang tersedia dan driver `psycopg` belum terpasang dalam lingkungan audit.
- **Migrasi data:** tidak dijalankan; tidak ada operasi tulis pada database pengguna.

## Prioritas rekomendasi

### P0 — sebelum dipakai di lingkungan bersama/publik

1. Instal dependensi pada virtual environment bersih dan jalankan semua tes.
2. Siapkan database PostgreSQL testing dan lakukan integration tests untuk register/login, duplicate email, CRUD film, watchlist ownership, transaksi, dan audit.
3. Pastikan konfigurasi production menggunakan `app.main:app` sebagai entry point kanonis; `backend.main:app` hanya alias kompatibilitas ke aplikasi yang sama.
4. Atur rate limit login dan pastikan respons error tidak membocorkan detail internal.
5. Buat migrasi data-integrity setelah pemeriksaan data aktual: NOT NULL, check rating/status/year, email case-insensitive unique, dan standardisasi timestamp.

### P1 — sebelum dianggap matang

1. Siapkan revision migrasi terkelola atau tetapkan SQL migrations sebagai satu-satunya standar operasional yang tercatat.
2. Tambahkan test untuk JWT invalid/expired, admin vs user, akses antar-user, response schema, dan database constraint.
3. Tentukan pencatatan audit dan kebijakan ketika penulisan log gagal.
4. Pertahankan pemeriksaan statis agar tidak ada query Supabase/PostgREST yang masuk kembali melalui modul kompatibilitas atau dependency.

### P2 — hanya bila masuk kebutuhan produk

- `reviews`, `favorites`, `collections`, `collection_movies`.
- Verifikasi email, reset password, refresh/revoke token, profil pengguna yang dapat diedit, multi-role/permission granular.
- Search ranking/pagination cursor/caching untuk katalog film besar.

## Sumber referensi teknis

- FastAPI — OAuth2/JWT and password hashing: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP Password Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- Passlib PBKDF2 defaults: https://passlib.readthedocs.io/en/stable/narr/hash-tutorial.html
- OWASP REST Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- SQLAlchemy Session Basics: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
