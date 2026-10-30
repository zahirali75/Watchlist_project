# MovieWatchlist — Redesign Frontend Black & Gold

## Cara menjalankan
```bash
# Backend (perlu .env sendiri; .env asli TIDAK disertakan di ZIP)
pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
# Frontend
cd frontend && cp .env.example .env && npm install && npm run dev   # http://localhost:5173
npm test && npm run lint && npm run build
```

## Rute (hash)
`#/home` (juga `#/discover` lama) · `#/movies` · `#/genres` · `#/watchlist` · `#/profile` · `#/movie/:id` · `#/my-reviews` · `#/admin` · `#/moderation` · `#/forgot-password` · `#/reset-password`

## Elemen layar → sumber data
| Elemen | Endpoint |
|---|---|
| Hero + Trending Now | `GET /movies?sort=rating_desc&limit=5` |
| New Releases | `GET /movies?sort=year_desc&limit=5` |
| Search header | `GET /movies?search=…` (judul saja) |
| Kartu & jumlah genre | `GET /movies?genre=X&limit=1` (`total` = jumlah nyata) |
| My Watchlist + filter status | `GET /watchlists/me?status=…&limit=4` |
| Ubah status / hapus | `PUT` / `DELETE /watchlists/{id}` |
| Add to Watchlist | `POST /watchlists` (409 = sudah ada) |
| Watchlist Summary & angka di chip | `GET /users/me/stats` |
| Login / Register / Logout / Refresh | `/auth/*` (client & AuthContext tidak diubah) |

## Perubahan backend (satu-satunya)
`GET /movies` menerima parameter **opsional** `sort` = `id` (default, perilaku lama) | `rating_desc` | `year_desc`.
Alasan: urutan rating/tahun harus dihitung di database, bukan dari 20–100 film pertama di browser.
Nilai dipetakan ke whitelist SQL (`SORT_ORDERS`), nilai lain → 422. File: `app/movies/{schemas,router,service,repository}.py`, tes: `tests/api/test_movies.py`.

## Berbeda dari gambar referensi (karena backend belum punya datanya)
- **Watch Trailer** dan **durasi** film: tidak ada kolom trailer/durasi → diganti tombol *View Details*, durasi disembunyikan.
- **Ikon notifikasi**: tidak ada fitur notifikasi → tidak ditampilkan.
- **Progress bar 67%**: tidak ada data progres → tidak ditampilkan.
- **Newsletter, Follow Us, Help, Privacy/Terms/Cookies**: tidak ada backend/halamannya → tidak ditampilkan.
- **Avatar foto**: tidak ada upload avatar → lingkaran dengan inisial nama.
- **Artwork hero**: tidak ada kolom backdrop → poster film (latar buram + poster tajam).
- **Placeholder search**: pencarian backend hanya judul, jadi tulisannya "Search movies by title…".
- Halaman lama (profil, ulasan, admin, detail) memakai tema yang sama tetapi teksnya masih Bahasa Indonesia.

## File berubah
Baru: `components/layout/{Logo,SearchBar,Footer}.jsx`, `components/home/{HeroBanner,HomePanels}.jsx`, `components/movie/MovieTile.jsx`, `features/home/HomePage.jsx`, `features/discover/GenresPage.jsx`, `lib/genres.js`.
Diubah: `styles.css` (ditulis ulang), `App.jsx`, `TopBar.jsx`, `AppShell.jsx`, `PageHeading.jsx`, `DiscoverPage.jsx` (kini halaman Movies), `AuthModal.jsx` (show/hide password), `api/movies.js` (`sort`), `hooks/useRoute.js`, `index.html`, `__tests__/ui.test.jsx`.

## Verifikasi yang dijalankan
- Backend `pytest tests/api`: 99 lulus (termasuk 2 tes `sort` baru). Tes integrasi DB tidak dijalankan (butuh PostgreSQL).
- Frontend `vitest`: 29 lulus · `eslint`: bersih · `vite build`: sukses.
- Browser (Chromium, 1536/820/390 px) terhadap router FastAPI asli dengan repository in-memory (database Supabase tidak terjangkau dari sandbox): tambah watchlist, duplikat 409, ubah status, filter, hapus, statistik, pencarian, state kosong, filter genre, detail, menu akun, logout, modal login — tanpa error JS dan tanpa scroll horizontal.
- **Belum diuji**: backend + PostgreSQL sungguhan, `npm run test:e2e`, halaman admin/ulasan secara visual, font Poppins dari Google Fonts (sandbox tanpa internet).
