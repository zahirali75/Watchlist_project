/**
 * Halaman watchlist. Menampilkan objek `movies` hasil JOIN dari
 * `GET /watchlists/me` — perhatikan backend mengirim KUNCI `movies` (bukan
 * `movie`), dan `media_type` sekarang ikut terisi karena sudah ada di tabel.
 */
import React from "react";
import { BookmarkPlus } from "lucide-react";

import { watchlistApi } from "../../api/index.js";
import Poster from "../../components/movie/Poster.jsx";
import { EmptyState, ErrorState, SkeletonGrid } from "../../components/ui/States.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useToast } from "../../context/ToastContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { formatYear } from "../../lib/format.js";
import { mediaTypeLabel } from "../../lib/mediaType.js";

const STATUS_LABELS = watchlistApi.WATCH_STATUS_LABELS;

export default function WatchlistPage({ onOpen, onBrowse }) {
  const { withAuth } = useAuth();
  const toast = useToast();

  const { data, loading, error, reload, setData } = useAsyncData(
    () => withAuth((token) => watchlistApi.listMyWatchlist({ token, limit: 100 })),
    [],
  );

  const rows = data?.items ?? [];

  async function changeStatus(itemId, status) {
    try {
      await withAuth((token) => watchlistApi.updateWatchlistItem(itemId, { status }, token));
      setData((current) => ({
        ...current,
        items: (current?.items ?? []).map((row) => (row.id === itemId ? { ...row, status } : row)),
      }));
      toast.success("Status diperbarui.");
    } catch (caught) {
      toast.error(caught.message);
    }
  }

  async function removeItem(itemId) {
    try {
      await withAuth((token) => watchlistApi.removeWatchlistItem(itemId, token));
      setData((current) => ({ ...current, items: (current?.items ?? []).filter((row) => row.id !== itemId) }));
      toast.success("Dihapus dari watchlist.");
    } catch (caught) {
      toast.error(caught.message);
    }
  }

  if (loading) return <SkeletonGrid count={4} className="skeleton-list" />;
  if (error) return <ErrorState error={error} onRetry={reload} title="Gagal memuat watchlist" />;

  if (!rows.length) {
    return (
      <EmptyState
        icon={BookmarkPlus}
        title="Watchlist masih kosong"
        description="Tambahkan judul dari halaman Discover untuk menyimpannya di sini."
        action={
          <button type="button" className="text-action" onClick={onBrowse}>
            Jelajahi katalog
          </button>
        }
      />
    );
  }

  return (
    <section className="list-table">
      <div className="table-head">
        <span>JUDUL</span>
        <span>JENIS / TAHUN</span>
        <span>STATUS</span>
        <span>AKSI</span>
      </div>
      {rows.map((row) => {
        const movie = row.movies || {};
        return (
          <article className="list-row" key={row.id}>
            <button type="button" className="list-title" onClick={() => onOpen(movie)}>
              <Poster item={movie} />
              <span>
                {movie.title || `Judul #${row.movie_id}`}
                <small>{movie.genre || "Tanpa genre"}</small>
              </span>
            </button>
            <span className="list-muted">
              {mediaTypeLabel(movie.media_type)} · {formatYear(movie.release_year)}
            </span>
            <select
              value={row.status}
              onChange={(event) => changeStatus(row.id, event.target.value)}
              aria-label={`Status untuk ${movie.title || row.movie_id}`}
            >
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option value={value} key={value}>
                  {label}
                </option>
              ))}
            </select>
            <button type="button" className="text-action danger" onClick={() => removeItem(row.id)}>
              Hapus
            </button>
          </article>
        );
      })}
    </section>
  );
}
