/**
 * Satu-satunya sumber kebenaran untuk istilah jenis tayangan.
 *
 * Backend menyimpan `movies.media_type` dengan nilai "movie" | "series"
 * (lihat app/movies/schemas.py → class MediaType). Versi frontend sebelumnya
 * mengirim "tv", dan backend menolaknya sebagai 422 — jadi nilai mentah backend
 * TIDAK BOLEH dipakai langsung sebagai nama tab di UI.
 *
 * Aturan: nilai API selalu lewat helper di file ini, label tampilan dipisah.
 */

export const MEDIA_TYPE = {
  all: "all",
  movie: "movie",
  series: "series",
};

/** Nilai yang boleh dikirim ke backend. "all" berarti parameter dihilangkan. */
export const API_MEDIA_TYPES = [MEDIA_TYPE.movie, MEDIA_TYPE.series];

/** Label untuk pengguna (Inggris, mengikuti bahasa antarmuka repo ini). */
export function mediaTypeLabel(value, { plural = false } = {}) {
  const singular = {
    [MEDIA_TYPE.movie]: "Film",
    [MEDIA_TYPE.series]: "Series",
  };
  if (value === MEDIA_TYPE.all || !value) return plural ? "All titles" : "Title";
  const label = singular[value] ?? "Title";
  return plural ? (value === MEDIA_TYPE.movie ? "Films" : "Series") : label;
}

/** Filter yang nilainya dihilangkan saat "all" dipilih. */
export function mediaTypeQuery(value) {
  return API_MEDIA_TYPES.includes(value) ? value : undefined;
}
