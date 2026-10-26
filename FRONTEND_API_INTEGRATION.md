# Integrasi Frontend — CineList API v2.0.0

Dokumen ini menjelaskan kontrak API yang benar-benar diimplementasikan. Semua contoh sudah dicocokkan dengan perilaku server yang berjalan.

## 1. Base URL dan CORS

| Lingkungan | Base URL | Catatan |
|---|---|---|
| Pengembangan | `http://localhost:8000` | `uvicorn app.main:app --port 8000` |
| Produksi | `https://<domain-api>` | Wajib HTTPS. Belum diuji. |

CORS: origin frontend harus terdaftar di `CORS_ORIGINS` (dipisah koma, tanpa `*`). Default: `http://localhost:5173,http://localhost:3000`. Origin lain ditolak pada preflight dengan 400 "Disallowed CORS origin". Setelah mengubah `.env`, restart server.

Header yang diizinkan: `Authorization`, `Content-Type`. Metode: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`.

## 2. Autentikasi

Kirim token di header:

```
Authorization: Bearer <accessToken>
```

Token berlaku `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60 menit). Tidak ada refresh token. Saat menerima 401, arahkan pengguna ke halaman login.

Simpan token di memori atau `sessionStorage`. Hindari `localStorage` bila memungkinkan, karena dapat dibaca skrip yang berhasil disisipkan (XSS). Jangan pernah merender input pengguna dengan `dangerouslySetInnerHTML`.

Role tidak boleh dipercaya dari token di sisi UI untuk keputusan keamanan. Server selalu memeriksa role dari database. Gunakan `role` di respons login hanya untuk menampilkan menu.

Backend ini tidak memakai Supabase Auth dan tidak menerima kunci Supabase. Jangan menyimpan kunci `anon` atau `service_role` Supabase di frontend untuk mengakses data; semua akses lewat API ini dengan token di atas.

## 3. Format respons

### Sukses

Sebagian besar respons sukses memakai envelope:

```json
{ "success": true, "message": "...", "data": { } }
```

Pengecualian yang harus diperhatikan frontend:

| Endpoint | Bentuk khusus |
|---|---|
| `POST /auth/register` dan `POST /auth/login` | Field di root: `success`, `message`, `userId`, `email`, `name`, `role`, `accessToken` (tidak ada `data`) |
| `GET /movies`, `GET /watchlists/me`, `GET /watchlists/{user_id}`, `GET /users`, `GET /audit-logs` | Envelope koleksi: `success`, `count`, `total`, `page`, `limit`, `data` (array) |
| `GET /watchlists/me/stats`, `GET /users/{id}/stats` | Field di root: `success`, `total`, `watched`, `watching`, `wantToWatch` |
| `GET /health` | `success`, `message`, `data` |

### Error

Semua error memakai bentuk yang sama:

```json
{
  "success": false,
  "message": "Pesan yang bisa ditampilkan",
  "data": { "errorCode": "KODE", "errorMeta": "...opsional..." }
}
```

Validasi (422) menyertakan `errorMeta` berupa daftar: `[{"location": ["body", "email"], "message": "..."}]`.

| HTTP | `errorCode` | Kapan |
|---|---|---|
| 400 | `BAD_REQUEST` | Aturan bisnis gagal, misalnya `limit` > 100, body update kosong, status null |
| 401 | `UNAUTHORIZED` | Token tidak ada, rusak, kedaluwarsa, akun dihapus, atau login gagal |
| 403 | `FORBIDDEN` | Login sah tetapi tidak punya izin |
| 404 | `NOT_FOUND` | Data tidak ada, atau rute tidak ada |
| 405 | `METHOD_NOT_ALLOWED` | Metode HTTP tidak didukung untuk rute |
| 409 | `CONFLICT` | Email sudah terdaftar, atau film sudah ada di watchlist |
| 422 | `VALIDATION_ERROR` | Input tidak lolos validasi |
| 429 | `TOO_MANY_REQUESTS` | Terlalu banyak login gagal. `errorMeta.retryAfterSeconds` berisi jeda. |
| 500 | `INTERNAL_ERROR` | Error tak terduga. Detail hanya di log server. |
| 502 | `UPSTREAM_ERROR` | Database tidak bisa diakses atau operasinya gagal |

## 4. Penanganan 401 dan 403

- **401:** hapus token dari penyimpanan, lalu arahkan ke login. Jangan mencoba mengulang request yang sama dengan token yang sama.
- **403:** tampilkan pesan "tidak punya akses". Jangan menghapus token.
- **429:** tampilkan pesan dengan `errorMeta.retryAfterSeconds`, dan nonaktifkan tombol login sementara.

## 5. Endpoint dan contoh

### Registrasi

`POST /auth/register` — publik.

```json
{ "email": "budi@example.com", "password": "rahasia123", "name": "Budi" }
```

- `password`: minimal 8 karakter.
- `name`: opsional, maksimal 255.
- Respons 201: `{ "success": true, "message": "Registrasi berhasil", "userId": "...", "email": "...", "name": "...", "role": "user", "accessToken": "..." }`
- Email sudah terdaftar: 409 dengan `message` "Email sudah terdaftar". Frontend boleh menampilkan pesan ini langsung.

### Login

`POST /auth/login` — publik. Body `{ "email", "password" }`. Respons 200 sama dengan registrasi, dengan `message` "Login berhasil".

Login salah: 401 "Email atau password salah" (pesan sama untuk email tidak dikenal).

### Film

`GET /movies?search=&genre=&page=1&limit=20` — publik.

```json
{ "success": true, "count": 2, "total": 15, "page": 1, "limit": 20, "data": [ { "id": 1, "title": "Inception", "release_year": 2010, "genre": "Sci-Fi", "director": "Christopher Nolan", "overview": "...", "poster_url": "https://...", "rating": 8.8, "created_at": "2026-10-24T09:02:04" } ] }
```

`GET /movies/{movie_id}` — publik. Respons: `{ "success": true, "message": "...", "data": { ... } }`.

`POST /movies`, `PUT /movies/{movie_id}`, `DELETE /movies/{movie_id}` — admin. Aturan input:

| Field | Aturan |
|---|---|
| `title` | wajib, 1–255 karakter |
| `release_year` | wajib, 1888–2100 |
| `genre` | wajib, 1–255 karakter |
| `director` | opsional, maks. 255 |
| `overview` | opsional, maks. 10.000 |
| `poster_url` | opsional, kosong atau diawali `http://` / `https://`, maks. 2048 |
| `rating` | 0–10 |

`PUT` adalah penggantian penuh: kirim semua field.

### Watchlist

`GET /watchlists/me?status=watching&page=1&limit=20` — login. Setiap item memuat objek `movies` (JOIN).

`POST /watchlists` — login.

```json
{ "movie_id": 1, "status": "watching", "notes": "tonton malam ini" }
```

- `status`: `want_to_watch` (default), `watching`, `watched`.
- `notes`: opsional, maks. 2.000.
- 201 saat berhasil. 404 bila film tidak ada. 409 bila film sudah ada di watchlist.

`PUT /watchlists/{watchlist_id}` — pemilik saja. Parsial: hanya field yang dikirim yang diubah.
- `notes: null` menghapus catatan.
- `status: null` menghasilkan 400.
- Body kosong `{}` menghasilkan 400.

`DELETE /watchlists/{watchlist_id}` — pemilik saja.

`GET /watchlists/me/stats` — login. Respons: `{ "success": true, "total": 3, "watched": 1, "watching": 1, "wantToWatch": 1 }`.

Ownership: item milik user lain menghasilkan 403, termasuk untuk admin.

### Admin

`GET /users?page=&limit=` — admin. Tanpa `password_hash`.
`GET /users/{user_id}` — admin. 404 bila tidak ada.
`GET /users/{user_id}/stats` — admin.
`GET /audit-logs?page=&limit=` — admin.
`GET /audit-logs/{log_id}` — admin.

## 6. Pagination

| Parameter | Default | Batas |
|---|---|---|
| `page` | 1 | 1–1.000.000 (lebih dari itu 422) |
| `limit` | 20 | 1–100 (lebih dari 100 menghasilkan 400); `0` berarti default |

Hitung halaman terakhir dengan `Math.ceil(total / limit)`. Frontend tidak perlu mengirim `offset`.

Urutan default: film berdasarkan `id` naik; watchlist dan user berdasarkan `created_at` turun.

## 7. Contoh integrasi (fetch)

```js
const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function api(path, { method = "GET", token, body } = {}) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json();
  if (!res.ok) {
    const error = new Error(json.message ?? "Permintaan gagal");
    error.status = res.status;
    error.code = json.data?.errorCode;
    error.meta = json.data?.errorMeta;
    throw error;
  }
  return json;
}

// Login
const { accessToken, role } = await api("/auth/login", {
  method: "POST",
  body: { email, password },
});

// Watchlist saya
const list = await api("/watchlists/me?limit=10", { token: accessToken });
```

Perhatikan: login mengembalikan `accessToken` di root respons, bukan di `data`.

## 8. Perubahan kontrak pada versi ini

### Non-breaking

- Header `Content-Type` dan bentuk sukses tidak berubah.
- Endpoint, method, path, nama field, dan tipe ID tidak berubah.
- `POST /login` dan `POST /users` (alias lama) tetap bekerja.

### Breaking kecil (hanya untuk input yang sebelumnya tidak valid)

| Perubahan | Dampak frontend |
|---|---|
| `poster_url` selain http/https ditolak (422) | Pastikan URL poster berformat `https://...` atau kosong |
| `overview` > 10.000 karakter ditolak (422) | Jarang terjadi; batasi input di form |
| `notes` > 2.000 karakter ditolak (422) | Tambahkan `maxLength={2000}` pada textarea |
| `page` > 1.000.000 ditolak (422) | Tidak mungkin terjadi pada pagination normal |
| Rute tidak ada dan metode salah sekarang memakai envelope `{success, message, data.errorCode}` | Jika kode lama membaca `detail`, ubah ke `message` |
| `GET /users/{id}` dengan id bukan UUID sekarang 404, bukan 400 | Tidak ada perubahan untuk id valid |

### Perilaku yang tetap dipertahankan dengan sengaja

- Registrasi dengan email terdaftar tetap 409 dengan pesan jelas. Ini memungkinkan enumerasi email (lihat laporan audit, S6).
- Admin tidak bisa melihat watchlist user lain (403).

## 9. Swagger dan OpenAPI

Buka `http://localhost:8000/docs` pada pengembangan. Di production (`APP_ENV=production`), `/docs`, `/redoc`, dan `/openapi.json` dimatikan.

Catatan: respons belum bertipe di OpenAPI, sehingga generator klien hanya menghasilkan tipe request. Tipe respons ditulis manual sesuai contoh di atas.

## 10. Checklist sebelum integrasi

- [ ] Base URL diatur lewat `VITE_API_URL` atau setara.
- [ ] Origin frontend ada di `CORS_ORIGINS` backend.
- [ ] Token dikirim sebagai `Authorization: Bearer`.
- [ ] Error 401 mengarahkan ke login; 403 menampilkan pesan izin.
- [ ] 429 pada login menampilkan jeda dari `retryAfterSeconds`.
- [ ] Pagination memakai `page` dan `limit` dan membaca `total`.
- [ ] Form film mengirim `poster_url` berformat `https://` atau kosong.
