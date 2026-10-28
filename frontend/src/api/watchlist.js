/** Endpoint watchlist (app/watchlists/router.py). */
import { requestData, requestList } from "./client.js";

/**
 * Daftar watchlist milik sendiri. Setiap baris memuat `movies` (objek film hasil
 * JOIN) sehingga UI tidak perlu memanggil /movies lagi.
 */
export function listMyWatchlist({ status, page, limit, token, signal } = {}) {
  return requestList("/watchlists/me", { token, signal, query: { status, page, limit } });
}

export function addToWatchlist({ movieId, status = "want_to_watch", notes }, token) {
  return requestData("/watchlists", {
    method: "POST",
    token,
    body: { movie_id: movieId, status, notes },
  });
}

/** Putusan parsial: kirim hanya field yang berubah. */
export function updateWatchlistItem(itemId, payload, token) {
  return requestData(`/watchlists/${itemId}`, { method: "PUT", token, body: payload });
}

export function removeWatchlistItem(itemId, token) {
  return requestData(`/watchlists/${itemId}`, { method: "DELETE", token });
}

export const WATCH_STATUSES = ["want_to_watch", "watching", "watched"];

export const WATCH_STATUS_LABELS = {
  want_to_watch: "Want to watch",
  watching: "Watching",
  watched: "Watched",
};
