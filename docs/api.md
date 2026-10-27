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

| Metode | Endpoint | Akses | Keterangan |
|---|---|---|---|
| GET | `/health` | Publik | Liveness, tidak menyentuh database |
| GET | `/health/db` | Publik | Readiness: `SELECT 1` |
| POST | `/auth/register` | Publik | 201; role selalu `user`; respons juga memuat `refreshToken` (di root, seperti `accessToken`) |
| POST | `/auth/login` | Publik | 200; 401 bila salah; 429 bila dibatasi |
| POST | `/auth/refresh` | Publik | Body `{refreshToken}` → access + refresh token baru. Token **dirotasi**: yang lama langsung tidak berlaku |
| POST | `/auth/logout` | Login | Body `{refreshToken}`; mencabut sesi perangkat ini saja |
| POST | `/auth/change-password` | Login | Body `{currentPassword, newPassword}`; password lama salah → 401; **semua sesi dicabut** |
| POST | `/auth/forgot-password` | Publik | Body `{email}`; jawaban selalu sama (tidak membocorkan email terdaftar) |
| POST | `/auth/reset-password` | Publik | Body `{token, newPassword}`; token sekali pakai, berlaku 30 menit |
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
| GET | `/users/me` | Login | **Profil sendiri** (sebelumnya hanya ada versi admin, jadi user biasa selalu 403). Tanpa `password_hash` |
| PUT | `/users/me` | Login | Ubah **nama** sendiri; email & role tidak bisa diubah dari sini |
| GET | `/users/me/stats` | Login | Bentuk sama dengan `/watchlists/me/stats` |
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
 "email": "budi@example.com", "name": "Budi", "role": "user", "accessToken": "<JWT>", "refreshToken": "<token>"}
```
`password`: min. 8 karakter. Login: body `{"email","password"}`, respons sama dengan "Login berhasil".

**Perpanjang sesi** `POST /auth/refresh`
```json
{"refreshToken": "<token dari login>"}
```
→ 200
```json
{"success": true, "message": "Sesi diperpanjang", "accessToken": "<JWT baru>", "refreshToken": "<token baru>"}
```
Access token kedaluwarsa dalam 60 menit; refresh token 14 hari. Setiap kali dipakai, refresh token **diganti** (rotasi) — simpan yang baru. Token yang sudah dipakai/dicabut → 401.

**Ganti password** `POST /auth/change-password` (header login wajib)
```json
{"currentPassword": "rahasia123", "newPassword": "rahasia456"}
```
→ 200 `{"success": true, "message": "Password berhasil diganti", "sessionsRevoked": 2}`. Seluruh sesi di semua perangkat langsung dicabut, jadi pengguna harus login ulang di perangkat lain.

**Lupa password** `POST /auth/forgot-password` → body `{"email": "..."}`, jawaban **sama** untuk email terdaftar maupun tidak (mencegah penebakan email). Bila SMTP belum diatur (`SMTP_HOST` kosong), email tidak dikirim dan isinya hanya ditulis ke log server — jalur ini tetap bisa dicoba saat pengembangan.
**Pasang password baru** `POST /auth/reset-password` → body `{"token": "<dari tautan email>", "newPassword": "..."}`. Token berlaku 30 menit dan hanya bisa dipakai sekali (400 bila dipakai ulang/kedaluwarsa).

**Profil sendiri** `GET /users/me` → `{"success": true, "message": "Profil berhasil diambil", "data": {"id", "name", "email", "role", "created_at"}}` — tanpa `password_hash`. `PUT /users/me` body `{"name": "Nama Baru"}`.

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
- **Sesi berlapis (sejak 27 Oktober 2026).** Access token (JWT) tetap berumur 60 menit; yang berumur panjang adalah **refresh token** (14 hari, `REFRESH_TOKEN_EXPIRE_DAYS`) dan disimpan di tabel `refresh_tokens` **hanya sebagai hash SHA-256**. Artinya bocornya isi tabel tidak langsung memberi akses. Refresh token **dirotasi** setiap dipakai dan dicabut saat logout, ganti password, atau lupa password (reset).
- **Endpoint lupa password tidak membocorkan email terdaftar**: `/auth/forgot-password` menjawab 200 dengan pesan sama untuk email yang ada maupun tidak. (Berbeda dari register, yang memang sengaja 409.)
- Modul `/users` dipisah dua: `/users/me` (login) dan `/users` + `/users/{id}` (admin). `/users/me` didaftarkan **lebih dulu** di `app/main.py` supaya tidak tertangkap pola `/users/{user_id}`.
