/** Endpoint katalog film (app/movies/router.py). */
import { requestData, requestList } from "./client.js";

/**
 * Daftar film dengan pencarian/filter/paginasi.
 * `sort`: "rating_desc" | "year_desc" (default urut id). `media_type` hanya dikirim bila bernilai "movie" atau "series" (helper mediaTypeQuery).
 */
export function listMovies({ search, genre, mediaType, sort, page, limit, signal } = {}) {
  return requestList("/movies", {
    signal,
    query: { search, genre, media_type: mediaType, sort, page, limit },
  });
}

export function getMovie(movieId, { signal } = {}) {
  return requestData(`/movies/${movieId}`, { signal });
}

/** Khusus admin. `payload` = field MovieCreate (lihat app/movies/schemas.py). */
export function createMovie(payload, token) {
  return requestData("/movies", { method: "POST", token, body: payload });
}

/** PUT = penggantian PENUH: kirim semua field, bukan hanya yang berubah. */
export function updateMovie(movieId, payload, token) {
  return requestData(`/movies/${movieId}`, { method: "PUT", token, body: payload });
}

export function deleteMovie(movieId, token) {
  return requestData(`/movies/${movieId}`, { method: "DELETE", token });
}
