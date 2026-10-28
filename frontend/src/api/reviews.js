/**
 * Endpoint ulasan (app/reviews/router.py — ditambahkan 28 Okt 2026, migrasi 0007).
 *
 * Catatan kontrak:
 * - Semua jalur butuh token; `GET /reviews/movie/{id}` juga (backend sengaja
 *   menutupnya supaya daftar penulis ulasan tidak bocor tanpa login).
 * - `PUT /reviews/{id}` bersifat PARSIAL (kirim hanya field yang berubah).
 * - Moderasi (/reviews/moderation + PATCH .../moderation) khusus admin.
 */
import { requestData, requestList } from "./client.js";

export function listMovieReviews(movieId, { page, limit, token, signal } = {}) {
  return requestList(`/reviews/movie/${movieId}`, { token, signal, query: { page, limit } });
}

export function listMyReviews({ page, limit, token, signal } = {}) {
  return requestList("/reviews/me", { token, signal, query: { page, limit } });
}

/** Admin saja. */
export function listReviewsForModeration({ page, limit, token, signal } = {}) {
  return requestList("/reviews/moderation", { token, signal, query: { page, limit } });
}

export function createReview({ movieId, rating, content }, token) {
  return requestData("/reviews", {
    method: "POST",
    token,
    body: { movie_id: movieId, rating, content },
  });
}

export function updateReview(reviewId, { rating, content }, token) {
  const body = {};
  if (rating !== undefined) body.rating = rating;
  if (content !== undefined) body.content = content;
  return requestData(`/reviews/${reviewId}`, { method: "PUT", token, body });
}

export function deleteReview(reviewId, token) {
  return requestData(`/reviews/${reviewId}`, { method: "DELETE", token });
}

/** Admin saja: sembunyikan/tampilkan kembali ulasan. */
export function moderateReview(reviewId, isHidden, token) {
  return requestData(`/reviews/${reviewId}/moderation`, {
    method: "PATCH",
    token,
    body: { is_hidden: isHidden },
  });
}
