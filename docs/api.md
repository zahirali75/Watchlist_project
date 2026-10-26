# Referensi API

Base URL development: `http://localhost:8000`. Semua body JSON. Swagger: `/docs`.
Header untuk endpoint login: `Authorization: Bearer <accessToken>`.

## Format respons
Sukses: `{"success": true, "message": "...", "data": ...}` (list menambah `count`, `total`, `page`, `limit`).
Pengecualian bentuk: register/login menaruh field langsung di root (`userId`, `accessToken`, ...) dan `*/stats` mengembalikan field statistik langsung di root.

Error (semua jenis, termasuk 422):
```json
{"success": false, "message": "Film dengan id 999 tidak ditemukan", "data": {"errorCode": "NOT_FOUND"}}
```
`data.errorMeta` opsional (detail tambahan). Tabel `errorCode`:

| HTTP | errorCode | Arti |
|---|---|---|
| 400 | BAD_REQUEST | Permintaan tidak valid (mis. `limit` > maks, body update kosong, ID tidak valid) |
| 401 | UNAUTHORIZED | Token tidak ada / rusak / kedaluwarsa / user sudah tidak ada; login salah |
| 403 | FORBIDDEN | Bukan admin, atau item milik user lain |
| 404 | NOT_FOUND | Data tidak ditemukan |
| 409 | CONFLICT | Duplikat (email, film di watchlist) |
| 422 | VALIDATION_ERROR | Validasi body/query gagal; `errorMeta` = daftar `{location, message}` |
| 429 | TOO_MANY_REQUESTS | Terlalu banyak login gagal; `errorMeta.retryAfterSeconds` |
| 500 | INTERNAL_ERROR | Bug server (detail hanya di log server) |
| 502 | UPSTREAM_ERROR | Database tidak dapat dihubungi/menolak |

## Pagination
Query `page` (≥1, default 1) dan `limit` (default 20, maks 100; melebihi → 400).

## Endpoint
Akses: **Publik**, **Login** (user/admin), **Admin**.

| Method | Path | Akses | Keterangan |
|---|---|---|---|
| GET | `/health` | Publik | Liveness (tanpa database) |
| GET | `/health/db` | Publik | Readiness: `SELECT 1` (**penambahan baru**) |
| POST | `/auth/register` | Publik | 201; role selalu `user` |
| POST | `/auth/login` | Publik | 200; 401 bila salah; 429 bila dibatasi |
| GET | `/movies` | Publik | Query: `search`, `genre`, `page`, `limit` |
| GET | `/movies/{movie_id}` | Publik | |
| POST | `/movies` | Admin | 201 |
| PUT | `/movies/{movie_id}` | Admin | Penggantian penuh (bukan PATCH) |
| DELETE | `/movies/{movie_id}` | Admin | |
| GET | `/watchlists/me` | Login | Query: `status`, `page`, `limit`; tiap item memuat `movies` |
| GET | `/watchlists/me/stats` | Login | `{total, watched, watching, wantToWatch}` |
| GET | `/watchlists/{user_id}` | Login | Hanya milik sendiri; selain itu 403 (admin pun) |
| POST | `/watchlists` | Login | 201; 404 film tak ada; 409 duplikat |
| PUT | `/watchlists/{id}` | Login (pemilik) | Hanya field yang dikirim; `notes: null` menghapus catatan; `status: null` → 400 |
| DELETE | `/watchlists/{id}` | Login (pemilik) | |
| GET | `/users` | Admin | Tanpa `password_hash` |
| GET | `/users/{user_id}` | Admin | 404 bila tidak ada |
| GET | `/users/{user_id}/stats` | Admin | 404 bila user tidak ada |
| GET | `/audit-logs` | Admin | |
| GET | `/audit-logs/{log_id}` | Admin | |

Alias lama tersembunyi dari Swagger (dipertahankan untuk kompatibilitas): `POST /login`, `POST /users` → sama dengan `/auth/login`, `/auth/register`.

## Contoh
**Register** `POST /auth/register`
```json
{"email": "budi@example.com", "password": "rahasia123", "name": "Budi"}
```
→ 201
```json
{"success": true, "message": "Registrasi berhasil", "userId": "3a7ae716-f386-4167-80b8-2f32b77494a8",
 "email": "budi@example.com", "name": "Budi", "role": "user", "accessToken": "<JWT>"}
```
`password`: min. 8 karakter. Login: body `{"email","password"}`, respons sama dengan "Login berhasil".

**Tambah film (admin)** `POST /movies`
```json
{"title": "Inception", "release_year": 2010, "genre": "Sci-Fi", "director": "Christopher Nolan",
 "overview": "Mimpi dalam mimpi", "poster_url": "", "rating": 8.8}
```
Aturan: `title`/`genre` wajib; `release_year` 1888–2100; `rating` 0–10; `poster_url` harus kosong atau diawali `http://`/`https://` (maks. 2048 karakter); `overview` maks. 10.000 karakter. → 201
```json
{"success": true, "message": "Film berhasil ditambahkan",
 "data": {"id": 1, "title": "Inception", "release_year": 2010, "genre": "Sci-Fi", "director": "Christopher Nolan",
          "overview": "Mimpi dalam mimpi", "poster_url": "", "rating": 8.8, "created_at": "2026-10-24T09:02:04.032355"}}
```

**Tambah ke watchlist** `POST /watchlists`
```json
{"movie_id": 1, "status": "watching", "notes": "tonton malam ini"}
```
`status`: `want_to_watch` (default) | `watching` | `watched`. → 201 `data`: `{id, user_id, movie_id, status, notes, created_at, updated_at}`.

**Daftar watchlist** `GET /watchlists/me` → item berbentuk `{..., "movies": {id, title, ...}}`.

## Catatan kontrak
- Timestamp `movies`/`watchlists`/`users` berupa ISO 8601 **tanpa zona waktu** (kolom `TIMESTAMP`); `audit_logs.created_at` memakai offset (`+00:00`). Anggap semuanya UTC.
- Nama field campuran: request/respons film & watchlist memakai `snake_case` (`release_year`, `movie_id`), sedangkan auth dan stats memakai `camelCase` (`accessToken`, `wantToWatch`). Ini kontrak asli dan dipertahankan.
- Response belum memakai `response_model` Pydantic (belum diperbaiki; lihat docs/audit-report.md).
- **Format error seragam untuk semua status**, termasuk rute yang tidak ada (404) dan metode yang salah (405): `{"success": false, "message": "...", "data": {"errorCode": "...", ...}}`. Sebelumnya 404/405 bawaan FastAPI memakai `{"detail": ...}`.
- `page` maksimal 1.000.000 (lebih dari itu → 422). `limit` maksimal 100 (lebih dari itu → 400).
- `notes` (watchlist) maksimal 2.000 karakter.
- Login dibatasi dua lapis (HTTP 429 dengan `errorMeta.retryAfterSeconds`): per (IP + email) dan per IP untuk semua email. Batas diatur `LOGIN_MAX_ATTEMPTS` (5) dan `LOGIN_IP_MAX_ATTEMPTS` (50) dalam jendela `LOGIN_WINDOW_SECONDS` (300 detik).
- `POST /auth/register` mengembalikan 409 "Email sudah terdaftar" (dengan email di `errorMeta`). Ini **sengaja dipertahankan** agar frontend dapat menampilkan pesan yang jelas; konsekuensinya email yang sudah terdaftar dapat diketahui dari endpoint ini. Login tetap memakai pesan generik.
