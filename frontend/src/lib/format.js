/** Pemformat tampilan yang dipakai di banyak halaman. */

export function formatRating(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(1) : "—";
}

export function formatYear(value) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? String(number) : "—";
}

export function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString();
}

/** Judul fallback saat judul terkait tidak dikirim backend. */
export function titleOrFallback(title, id) {
  return title || `Title #${id}`;
}

/** Genres backend berupa teks ("Crime, Drama"), bukan larik. */
export function genreList(genre) {
  return String(genre || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

export function joinGenres(genre, limit = 3) {
  const list = genreList(genre);
  return list.length ? list.slice(0, limit).join(" · ") : "Unclassified";
}

/** Angka dengan nol di depan, dipakai untuk nomor kartu. */
export function padId(value, size = 3) {
  return String(value ?? "").padStart(size, "0");
}
