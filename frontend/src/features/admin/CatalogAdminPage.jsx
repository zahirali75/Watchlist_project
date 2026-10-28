/**
 * Halaman katalog admin: tambah/ubah/hapus judul.
 *
 * BUG KONTRAK YANG DIPERBAIKI DI SINI: formulir versi lama mengirim `tmdb_id`,
 * `genres`, `release_date`, dan `poster_path`, serta mengirim `media_type: "tv"`.
 * Keempat field pertama bukan bagian skema backend, dan "tv" ditolak validasi
 * (`MediaType` hanya menerima "movie" | "series"), sehingga setiap penambahan
 * judul gagal. Formulir sekarang hanya mengirim field yang benar-benar ada di
 * `app/movies/schemas.py`, ditambah `director` yang sebelumnya malah tidak ada
 * di formulir meski didukung backend.
 */
import React, { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";

import { moviesApi, systemApi } from "../../api/index.js";
import MovieCard from "../../components/movie/MovieCard.jsx";
import { EmptyState, ErrorState, SkeletonGrid } from "../../components/ui/States.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useToast } from "../../context/ToastContext.jsx";
import { useAsyncData, useDebounced } from "../../hooks/useAsyncData.js";
import { formatDate } from "../../lib/format.js";
import { MEDIA_TYPE, mediaTypeQuery } from "../../lib/mediaType.js";

const EMPTY_FORM = {
  title: "",
  release_year: new Date().getFullYear(),
  genre: "",
  director: "",
  overview: "",
  poster_url: "",
  rating: 0,
  media_type: MEDIA_TYPE.movie,
};

export default function CatalogAdminPage({ onOpen }) {
  const { withAuth } = useAuth();
  const toast = useToast();

  const [search, setSearch] = useState("");
  const [mediaType, setMediaType] = useState(MEDIA_TYPE.all);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const debouncedSearch = useDebounced(search, 350);

  const catalog = useAsyncData(
    ({ signal }) =>
      moviesApi.listMovies({
        search: debouncedSearch || undefined,
        mediaType: mediaTypeQuery(mediaType),
        limit: 100,
        signal,
      }),
    [debouncedSearch, mediaType],
  );

  const audit = useAsyncData(
    () => withAuth((token) => systemApi.listAuditLogs({ token, limit: 12 })),
    [],
  );

  const items = catalog.data?.items ?? [];

  useEffect(() => {
    if (catalog.error?.isUnauthorized) toast.error("Sesi berakhir. Silakan masuk lagi.");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalog.error]);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function resetForm() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setFormError("");
  }

  function startEdit(item) {
    setEditingId(item.id);
    setForm({
      title: item.title ?? "",
      release_year: item.release_year ?? new Date().getFullYear(),
      genre: item.genre ?? "",
      director: item.director ?? "",
      overview: item.overview ?? "",
      poster_url: item.poster_url ?? "",
      rating: Number(item.rating ?? 0),
      media_type: item.media_type ?? MEDIA_TYPE.movie,
    });
    setFormError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function validate() {
    if (!form.title.trim()) return "Judul wajib diisi.";
    const year = Number(form.release_year);
    if (!Number.isInteger(year) || year < 1888 || year > 2100) return "Tahun rilis harus antara 1888 dan 2100.";
    const rating = Number(form.rating);
    if (!Number.isFinite(rating) || rating < 0 || rating > 10) return "Rating harus antara 0 dan 10.";
    if (!form.genre.trim()) return "Genre wajib diisi (backend memakai satu kolom teks).";
    if (form.poster_url && !/^https?:\/\//i.test(form.poster_url.trim())) {
      return "URL poster harus dimulai dengan http:// atau https://.";
    }
    return "";
  }

  async function onSubmit(event) {
    event.preventDefault();
    const localError = validate();
    if (localError) {
      setFormError(localError);
      return;
    }
    setFormError("");
    setSaving(true);

    // HANYA field yang ada di MovieCreate/MovieUpdate. PUT = penggantian penuh,
    // jadi seluruh field dikirim (bukan hanya yang berubah).
    const payload = {
      title: form.title.trim(),
      release_year: Number(form.release_year),
      genre: form.genre.trim(),
      director: form.director.trim(),
      overview: form.overview,
      poster_url: form.poster_url.trim(),
      rating: Number(form.rating),
      media_type: form.media_type,
    };

    try {
      await withAuth((token) =>
        editingId ? moviesApi.updateMovie(editingId, payload, token) : moviesApi.createMovie(payload, token),
      );
      toast.success(editingId ? "Judul diperbarui." : "Judul ditambahkan.");
      resetForm();
      catalog.reload();
      audit.reload();
    } catch (error) {
      const perField = error?.fieldMessage?.("title") || error?.fieldMessage?.("release_year") || "";
      setFormError(perField || error.message);
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(item) {
    if (!window.confirm(`Hapus "${item.title}" dari katalog?`)) return;
    try {
      await withAuth((token) => moviesApi.deleteMovie(item.id, token));
      toast.success("Judul dihapus.");
      if (editingId === item.id) resetForm();
      catalog.reload();
      audit.reload();
    } catch (error) {
      toast.error(error.message);
    }
  }

  return (
    <div>
      <form className="admin-form" onSubmit={onSubmit}>
        <div className="form-title">
          <ShieldCheck size={17} aria-hidden="true" /> {editingId ? `UBAH JUDUL #${editingId}` : "TAMBAH KE KATALOG"}
        </div>
        <div className="admin-grid">
          <input
            required
            maxLength={255}
            placeholder="Judul"
            aria-label="Judul"
            value={form.title}
            onChange={(event) => update("title", event.target.value)}
          />
          <select
            value={form.media_type}
            aria-label="Jenis tayangan"
            onChange={(event) => update("media_type", event.target.value)}
          >
            <option value={MEDIA_TYPE.movie}>Film</option>
            <option value={MEDIA_TYPE.series}>Series</option>
          </select>
          <input
            required
            type="number"
            min="1888"
            max="2100"
            placeholder="Tahun"
            aria-label="Tahun rilis"
            value={form.release_year}
            onChange={(event) => update("release_year", event.target.value)}
          />
          <input
            required
            placeholder="Genre (pisahkan dengan koma)"
            aria-label="Genre"
            value={form.genre}
            onChange={(event) => update("genre", event.target.value)}
          />
          <input
            placeholder="Sutradara"
            aria-label="Sutradara"
            value={form.director}
            onChange={(event) => update("director", event.target.value)}
          />
          <input
            type="number"
            min="0"
            max="10"
            step="0.1"
            placeholder="Rating"
            aria-label="Rating"
            value={form.rating}
            onChange={(event) => update("rating", event.target.value)}
          />
        </div>
        <input
          placeholder="URL poster (http/https) atau kosongkan"
          aria-label="URL poster"
          value={form.poster_url}
          onChange={(event) => update("poster_url", event.target.value)}
        />
        <textarea
          maxLength={10000}
          placeholder="Sinopsis"
          aria-label="Sinopsis"
          value={form.overview}
          onChange={(event) => update("overview", event.target.value)}
        />
        {formError ? (
          <p className="form-error" role="alert">
            {formError}
          </p>
        ) : null}
        <div className="admin-form-actions">
          <button className="primary-button" type="submit" disabled={saving}>
            {saving ? "Menyimpan…" : editingId ? "Simpan perubahan" : "Tambah judul"}
          </button>
          {editingId ? (
            <button type="button" className="text-action" onClick={resetForm}>
              Batal
            </button>
          ) : null}
        </div>
      </form>

      <section className="admin-toolbar">
        <label className="search-control">
          <span className="search-glyph" aria-hidden="true" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Cari judul di katalog"
            aria-label="Cari judul di katalog"
            type="search"
          />
        </label>
        <div className="segmented" role="group" aria-label="Filter jenis tayangan">
          {[MEDIA_TYPE.all, MEDIA_TYPE.movie, MEDIA_TYPE.series].map((value) => (
            <button
              type="button"
              key={value}
              className={mediaType === value ? "selected" : ""}
              aria-pressed={mediaType === value}
              onClick={() => setMediaType(value)}
            >
              {value === MEDIA_TYPE.all ? "Semua" : value === MEDIA_TYPE.movie ? "Film" : "Series"}
            </button>
          ))}
        </div>
        <span className="result-count">
          {catalog.loading ? "MEMUAT…" : `${catalog.data?.total ?? 0} JUDUL`}
        </span>
      </section>

      {catalog.error ? <ErrorState error={catalog.error} onRetry={catalog.reload} /> : null}
      {catalog.loading && !items.length ? <SkeletonGrid count={10} /> : null}

      {!catalog.loading && !catalog.error && !items.length ? (
        <EmptyState title="Tidak ada judul" description="Ubah kata kunci pencarian atau filter jenis tayangan." />
      ) : null}

      {items.length ? (
        <section className="catalog-grid">
          {items.map((item, index) => (
            <MovieCard
              key={item.id}
              item={item}
              index={index}
              admin
              onOpen={onOpen}
              onEdit={startEdit}
              onDelete={onDelete}
            />
          ))}
        </section>
      ) : null}

      <section className="audit-panel">
        <h2>Jejak audit terbaru</h2>
        <p className="panel-note">Diambil dari GET /audit-logs (khusus admin).</p>
        {audit.loading ? (
          <p className="list-muted">Memuat…</p>
        ) : audit.error ? (
          <p className="form-error">{audit.error.message}</p>
        ) : (audit.data?.items ?? []).length ? (
          <ul className="audit-list">
            {audit.data.items.map((log) => (
              <li key={log.id}>
                <span className="audit-action">{log.action}</span>
                <span className="audit-context">{log.context || log.entity || "—"}</span>
                <small>{formatDate(log.created_at)}</small>
              </li>
            ))}
          </ul>
        ) : (
          <p className="list-muted">Belum ada catatan audit.</p>
        )}
      </section>
    </div>
  );
}
