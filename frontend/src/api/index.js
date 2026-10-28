/**
 * Titik masuk API frontend. Komponen tidak boleh memanggil fetch langsung —
 * semua lewat modul di bawah supaya URL, method, dan bentuk payload terkumpul di
 * satu tempat dan mudah ditelusuri saat ada perubahan backend.
 *
 * Pemetaan modul → router backend:
 *   auth.js      → app/auth/router.py, app/users/me_router.py
 *   movies.js    → app/movies/router.py
 *   watchlist.js → app/watchlists/router.py
 *   reviews.js   → app/reviews/router.py
 *   system.js    → app/health/router.py
 *
 * Endpoint internal (mis. /audit-logs milik admin, /users/{id}) sengaja tidak
 * dipakai antarmuka pengguna. Halaman Admin yang ada memakai /audit-logs untuk
 * menampilkan jejak audit terbaru.
 */
export { API_BASE, ApiError, request, requestData, requestList } from "./client.js";
export * as authApi from "./auth.js";
export * as moviesApi from "./movies.js";
export * as watchlistApi from "./watchlist.js";
export * as reviewsApi from "./reviews.js";
export * as systemApi from "./system.js";
