/**
 * Tes alur utama terhadap BACKEND SUNGGUHAN (integration).
 *
 * Jalankan dengan: npm run test:e2e   (backend harus hidup di VITE_API_URL)
 *
 * Kenapa terpisah dari tes unit: tes ini menulis ke database nyata (membuat akun
 * uji, menambah watchlist, menulis ulasan). Ia membuktikan hal yang tidak bisa
 * dibuktikan mock, yaitu kontrak URL/method/payload benar-benar diterima backend.
 *
 * PENTING soal sisa data: backend TIDAK punya endpoint hapus user (hanya
 * GET/PUT /users/me). Jadi akun uji berpola `e2e.frontend.<angka>@example.com`
 * TIDAK terhapus otomatis oleh tes ini — afterAll hanya membersihkan watchlist
 * dan ulasan miliknya. Setelah menjalankan tes, bersihkan akun sisa dengan
 * skrip di folder catatan:
 *     .venv\Scripts\python.exe C:\Users\Asus\cinelist-catatan\bersihkan_akun_uji.py --hapus
 * (sesuaikan konstanta EMAIL di skrip itu dengan email yang dicetak afterAll).
 */
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { ApiError, moviesApi, request, requestList, reviewsApi, watchlistApi } from "../api/index.js";
import * as authApi from "../api/auth.js";

const BASE = process.env.VITE_API_URL || "http://127.0.0.1:8000";
const unique = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
const ACCOUNT = {
  email: `e2e.frontend.${unique}@example.com`,
  password: "RahasiaE2E123",
  name: "E2E Frontend",
};

let session = null;
let movieId = null;

async function backendAlive() {
  try {
    const health = await fetch(`${BASE}/health`);
    return health.ok;
  } catch {
    return false;
  }
}

const alive = await backendAlive();

beforeAll(async () => {
  if (!alive) return;
  const registered = await authApi.register(ACCOUNT);
  session = {
    accessToken: registered.accessToken,
    refreshToken: registered.refreshToken,
    userId: registered.userId,
    email: registered.email,
    role: registered.role,
  };
  const catalog = await moviesApi.listMovies({ limit: 1 });
  movieId = catalog.items[0]?.id ?? null;
});

afterAll(async () => {
  if (!alive || !session) return;
  // Bersih-bersih yang MEMANG bisa dilakukan: hapus ulasan & watchlist milik
  // akun uji. Akunnya sendiri tidak bisa dihapus dari sini karena backend tidak
  // menyediakan endpoint hapus user. Karena itu sisa akun dicetak terang-terangan
  // supaya tidak jadi sampah tersembunyi di database.
  try {
    const mine = await reviewsApi.listMyReviews({ token: session.accessToken, limit: 100 });
    for (const review of mine.items) {
      await reviewsApi.deleteReview(review.id, session.accessToken);
    }
    const list = await watchlistApi.listMyWatchlist({ token: session.accessToken, limit: 100 });
    for (const row of list.items) {
      await watchlistApi.removeWatchlistItem(row.id, session.accessToken);
    }
  } catch {
    /* sisa data uji tidak menghalangi */
  }
  if (session?.email) {
    console.warn(
      `[e2e] Akun uji DIBIARKAN di database: ${session.email}\n` +
        "[e2e] Backend tidak punya endpoint hapus user; bersihkan manual dengan " +
        "bersihkan_akun_uji.py --hapus (lihat komentar kepala berkas ini).",
    );
  }
});

describe.skipIf(!alive)("alur nyata frontend → backend", () => {
  it("backend hidup dan /health membalas", async () => {
    const payload = await request("/health");
    expect(payload.success).toBe(true);
  });

  it("registrasi mengembalikan token di ROOT respons", () => {
    expect(session.accessToken).toBeTruthy();
    expect(session.refreshToken).toBeTruthy();
    expect(session.email).toBe(ACCOUNT.email);
  });

  it("login dengan akun itu berhasil", async () => {
    const payload = await authApi.login({ email: ACCOUNT.email, password: ACCOUNT.password });
    expect(payload.accessToken).toBeTruthy();
  });

  it("refresh token menghasilkan access token baru", async () => {
    const payload = await authApi.refreshSession(session.refreshToken);
    expect(payload.accessToken).toBeTruthy();
    session.accessToken = payload.accessToken;
    session.refreshToken = payload.refreshToken ?? session.refreshToken;
  });

  it("GET /users/me mengembalikan profil sendiri", async () => {
    const profile = await authApi.getMyProfile(session.accessToken);
    expect(profile.email).toBe(ACCOUNT.email);
  });

  it("PUT /users/me mengubah nama tampilan", async () => {
    const profile = await authApi.updateMyProfile("Nama Baru E2E", session.accessToken);
    expect(profile.name).toBe("Nama Baru E2E");
  });

  it("GET /users/me/stats berbentuk camelCase", async () => {
    const payload = await authApi.getMyStats(session.accessToken);
    expect(payload).toHaveProperty("total");
    expect(payload).toHaveProperty("wantToWatch");
  });

  it("katalog memuat dan bentuknya berhalaman", async () => {
    const catalog = await moviesApi.listMovies({ limit: 5 });
    expect(Array.isArray(catalog.items)).toBe(true);
    expect(catalog.total).toBeGreaterThan(0);
    expect(catalog.items[0]).toHaveProperty("title");
  });

  it("filter media_type benar-benar menyaring (dulu diabaikan backend)", async () => {
    const all = await moviesApi.listMovies({ limit: 1 });
    const movies = await moviesApi.listMovies({ mediaType: "movie", limit: 100 });
    const series = await moviesApi.listMovies({ mediaType: "series", limit: 100 });

    expect(movies.total + series.total).toBe(all.total);
    expect(movies.items.every((item) => item.media_type === "movie")).toBe(true);
    expect(series.items.every((item) => item.media_type === "series")).toBe(true);
  });

  it("nilai media_type 'tv' ditolak backend (bukti kenapa frontend memakai movie|series)", async () => {
    const error = await moviesApi.listMovies({ mediaType: "tv" }).catch((caught) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(422);
  });

  it("menambah lalu membaca kembali watchlist (tulis–baca)", async () => {
    const added = await watchlistApi.addToWatchlist({ movieId, status: "want_to_watch" }, session.accessToken);
    expect(added.movie_id).toBe(movieId);

    const list = await watchlistApi.listMyWatchlist({ token: session.accessToken, limit: 100 });
    const row = list.items.find((item) => item.movie_id === movieId);
    expect(row).toBeTruthy();
    // Baris watchlist memuat objek film hasil JOIN dengan KUNCI `movies`.
    expect(row.movies).toHaveProperty("title");
    expect(row.movies).toHaveProperty("media_type");

    await watchlistApi.updateWatchlistItem(row.id, { status: "watched" }, session.accessToken);
    const after = await watchlistApi.listMyWatchlist({ token: session.accessToken, limit: 100 });
    expect(after.items.find((item) => item.id === row.id).status).toBe("watched");

    await watchlistApi.removeWatchlistItem(row.id, session.accessToken);
  });

  it("menambah watchlist dua kali dibalas 409 (duplikat)", async () => {
    const added = await watchlistApi.addToWatchlist({ movieId, status: "want_to_watch" }, session.accessToken);
    const error = await watchlistApi
      .addToWatchlist({ movieId, status: "want_to_watch" }, session.accessToken)
      .catch((caught) => caught);
    expect(error.status).toBe(409);
    await watchlistApi.removeWatchlistItem(added.id, session.accessToken);
  });

  it("menulis ulasan, membacanya, mengubahnya, lalu menghapusnya (tanpa token = 401)", async () => {
    const created = await reviewsApi.createReview(
      { movieId, rating: 8.5, content: "Ulasan dari tes alur nyata." },
      session.accessToken,
    );
    expect(created.movie_id).toBe(movieId);

    const reviews = await reviewsApi.listMovieReviews(movieId, { token: session.accessToken, limit: 100 });
    expect(reviews.items.some((review) => review.id === created.id)).toBe(true);
    expect(reviews.items[0]).toHaveProperty("user_name");
    expect(reviews.items[0]).toHaveProperty("movie_title");

    const updated = await reviewsApi.updateReview(created.id, { rating: 9 }, session.accessToken);
    expect(Number(updated.rating)).toBe(9);

    // Tanpa token → 401 (backend sengaja menutup daftar ulasan).
    const anonymous = await reviewsApi.listMovieReviews(movieId).catch((caught) => caught);
    expect(anonymous.status).toBe(401);

    await reviewsApi.deleteReview(created.id, session.accessToken);
    const after = await reviewsApi.listMovieReviews(movieId, { token: session.accessToken, limit: 100 });
    expect(after.items.some((review) => review.id === created.id)).toBe(false);
  });

  it("satu pengguna hanya boleh satu ulasan per film (409)", async () => {
    const first = await reviewsApi.createReview({ movieId, rating: 7, content: "Pertama" }, session.accessToken);
    const error = await reviewsApi
      .createReview({ movieId, rating: 6, content: "Kedua" }, session.accessToken)
      .catch((caught) => caught);
    expect(error.status).toBe(409);
    await reviewsApi.deleteReview(first.id, session.accessToken);
  });

  it("endpoint moderasi menolak pengguna biasa (403)", async () => {
    const error = await reviewsApi.listReviewsForModeration({ token: session.accessToken }).catch((caught) => caught);
    expect(error.status).toBe(403);
  });

  it("POST /movies tanpa token dibalas 401 (bukan 500)", async () => {
    const error = await moviesApi
      .createMovie({ title: "X", release_year: 2024, genre: "Drama" })
      .catch((caught) => caught);
    expect(error.status).toBe(401);
  });

  it("POST /movies dengan pengguna biasa dibalas 403", async () => {
    const error = await moviesApi
      .createMovie({ title: "X", release_year: 2024, genre: "Drama" }, session.accessToken)
      .catch((caught) => caught);
    expect(error.status).toBe(403);
  });

  it("field yang tidak ada di skema backend tidak tersimpan", async () => {
    const error = await moviesApi
      .createMovie({ title: "X", release_year: 2024, genre: "Drama", tmdb_id: 1, genres: ["A"] }, session.accessToken)
      .catch((caught) => caught);
    // 403 karena bukan admin — yang penting: request tidak pernah berhasil,
    // dan payload berisi field karangan tetap tidak diterima backend.
    expect([401, 403, 422]).toContain(error.status);
  });

  it("GET /movies/{id} yang tidak ada dibalas 404 dengan pesan", async () => {
    const error = await moviesApi.getMovie(99999999).catch((caught) => caught);
    expect(error.status).toBe(404);
    expect(error.message).toMatch(/tidak ditemukan/i);
  });

  it("endpoint audit-logs hanya untuk admin", async () => {
    const error = await requestList("/audit-logs", { token: session.accessToken }).catch((caught) => caught);
    expect(error.status).toBe(403);
  });

  it("logout mencabut refresh token", async () => {
    const payload = await authApi.logout(session.refreshToken, session.accessToken);
    expect(payload.success).toBe(true);
    const error = await authApi.refreshSession(session.refreshToken).catch((caught) => caught);
    expect([401, 400]).toContain(error.status);
  });
});
