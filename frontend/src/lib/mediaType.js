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

/**
 * Chip filter jenis tayangan (dipakai DiscoverPage).
 *
 * Dulu filter memakai bentuk jamak ("Films") sementara kartu dan halaman admin
 * memakai "Film" — satu jenis tampil dengan dua ejaan berbeda di layar yang
 * sama. Sekarang keduanya merujuk daftar ini, jadi ejaannya tidak bisa lagi
 * menyimpang. Urutannya: paling umum lebih dulu (Semua → Film → Series).
 */
export const MEDIA_TYPE_FILTERS = [
  { value: MEDIA_TYPE.all, label: "Semua" },
  { value: MEDIA_TYPE.movie, label: "Film" },
  { value: MEDIA_TYPE.series, label: "Series" },
];

/** Label satu judul (kartu, detail, baris watchlist). Selalu bentuk tunggal. */
export function mediaTypeLabel(value) {
  const labels = {
    [MEDIA_TYPE.movie]: "Film",
    [MEDIA_TYPE.series]: "Series",
  };
  return labels[value] ?? "Judul";
}

/** Filter yang nilainya dihilangkan saat "all" dipilih. */
export function mediaTypeQuery(value) {
  return API_MEDIA_TYPES.includes(value) ? value : undefined;
}
