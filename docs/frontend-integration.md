# Integrasi Frontend (React / Vue / lainnya)

Semua contoh sesuai kontrak di [api.md](api.md) dan diuji terhadap server asli.

## 1. Konfigurasi
| | Development | Production |
|---|---|---|
| Base URL | `http://localhost:8000` | `https://api.domain-anda.com` |
| `CORS_ORIGINS` backend | `http://localhost:5173,http://localhost:3000` | domain frontend saja, mis. `https://app.domain-anda.com` |
| Swagger `/docs` | aktif | mati (`APP_ENV=production`) |

Vite: `.env` → `VITE_API_URL=http://localhost:8000`. Frontend di origin yang tidak terdaftar di `CORS_ORIGINS` akan diblokir browser (error CORS) — tambahkan origin-nya ke `.env` backend lalu restart. Gunakan HTTPS di production.

## 2. Klien kecil (fetch)
```js
const API = import.meta.env.VITE_API_URL;

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.message ?? `HTTP ${status}`);
    this.status = status;
    this.code = body?.data?.errorCode;   // mis. "CONFLICT"
    this.meta = body?.data?.errorMeta;   // 422: [{location, message}]
  }
}

export async function api(path, { method = "GET", body, token } = {}) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, json);
  return json;
}
```

## 3. Registrasi & login
```js
const reg = await api("/auth/register", { method: "POST", body: { email, password, name } });
const login = await api("/auth/login", { method: "POST", body: { email, password } });
// login = { success, message, userId, email, name, role, accessToken }
```
Token berlaku `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60 menit). Saat 401 → coba `POST /auth/refresh` dengan refresh token yang disimpan; bila refresh juga 401 (kedaluwarsa/dicabut) → arahkan ke halaman login.

**Penyimpanan token:**
- SPA sederhana/tugas kuliah: simpan di memori (state) dan, bila perlu bertahan saat refresh, `sessionStorage`. `localStorage` rentan dibaca skrip XSS; pastikan tidak ada `dangerouslySetInnerHTML` dari input pengguna.
- Production: pertimbangkan cookie `HttpOnly` lewat backend-for-frontend (butuh perubahan backend; belum ada di proyek ini).
- Jangan pernah menaruh `SECRET_KEY` atau kredensial database di frontend.

## 4. Film (publik)
```js
const { data, total, page, limit } = await api(`/movies?search=incep&genre=Sci&page=1&limit=20`);
const one = await api(`/movies/1`);   // one.data
```

## 5. Watchlist (login)
```js
const token = login.accessToken;
await api("/watchlists", { method: "POST", token, body: { movie_id: 1, status: "watching", notes: "malam ini" } });
const mine = await api("/watchlists/me?status=watching", { token });   // mine.data[i].movies.title
await api("/watchlists/5", { method: "PUT", token, body: { status: "watched" } });
await api("/watchlists/5", { method: "PUT", token, body: { notes: null } });  // hapus catatan
await api("/watchlists/5", { method: "DELETE", token });
const stats = await api("/watchlists/me/stats", { token }); // {total, watched, watching, wantToWatch}
```

## 6. Admin
Tombol/menu admin berdasarkan `login.role === "admin"` hanya soal tampilan; **keamanan dijaga server** (403 untuk non-admin). `POST/PUT/DELETE /movies`, `/users`, `/audit-logs` butuh admin. Role dibaca dari database di setiap request, jadi pencabutan hak admin langsung berlaku.

## 7. Menangani error
| Status | `errorCode` | Tindakan di UI |
|---|---|---|
| 401 | UNAUTHORIZED | Hapus token, ke halaman login (kecuali di form login: tampilkan "email/password salah") |
| 403 | FORBIDDEN | Tampilkan "tidak punya akses" |
| 404 | NOT_FOUND | Tampilkan data tidak ditemukan |
| 409 | CONFLICT | Mis. "Film sudah ada di watchlist"; `meta.movieId` |
| 422 | VALIDATION_ERROR | Petakan `meta[].location` (mis. `["body","email"]`) ke field form |
| 429 | TOO_MANY_REQUESTS | Nonaktifkan tombol login selama `meta.retryAfterSeconds` |
| 400 | BAD_REQUEST | Tampilkan `message` |
| 500/502 | INTERNAL_ERROR / UPSTREAM_ERROR | "Terjadi kesalahan, coba lagi nanti" (jangan tampilkan detail teknis) |

```js
try { await api("/watchlists", { method: "POST", token, body }); }
catch (e) {
  if (e.code === "CONFLICT") alert("Film sudah ada di watchlist");
  else if (e.status === 401) logout();
  else if (e.status === 422) showFieldErrors(e.meta);
}
```

## 8. Axios (alternatif)
```js
import axios from "axios";
export const http = axios.create({ baseURL: import.meta.env.VITE_API_URL });
http.interceptors.request.use(cfg => { const t = sessionStorage.getItem("token"); if (t) cfg.headers.Authorization = `Bearer ${t}`; return cfg; });
http.interceptors.response.use(r => r, err => { if (err.response?.status === 401) sessionStorage.removeItem("token"); return Promise.reject(err); });
// error body: err.response.data.data.errorCode
```

## 9. Membaca Swagger / OpenAPI
Buka `/docs` (development) → **Authorize** → tempel `accessToken` (tanpa kata `Bearer`) → coba endpoint. Skema mentah: `/openapi.json`.

**Penting bila backend ini dijadikan acuan frontend:** yang bertipe di OpenAPI baru **body request** (skema `RegisterUser`, `MovieCreate`, dll.). **Bentuk respons belum ada tipenya** — `response_model` belum dipakai di satu router pun, sehingga setiap respons muncul sebagai `{}` di `/openapi.json`. Konsekuensinya generator klien otomatis (seperti `openapi-typescript`) hanya menghasilkan tipe request; tipe respons harus ditulis manual mengikuti tabel contoh di [api.md](api.md).

## 10. Format data yang perlu diperhatikan
- ID user = UUID string; ID film/watchlist/audit = integer.
- `rating` = angka desimal 0–10; `release_year` = integer.
- Waktu = ISO 8601 (anggap UTC; `movies`/`watchlists` tanpa offset).
- Field film/watchlist `snake_case`; field auth/stats `camelCase`.
