/**
 * Halaman Discover (beranda). Menangani tab Discover/Film/Series sekaligus
 * pencarian dan filter genre.
 *
 * Catatan integrasi: parameter `media_type` dulu dikirim sebagai "tv" sehingga
 * ditolak backend dengan 422 dan tab Series tidak pernah benar-benar menyaring.
 * Sekarang nilai diambil dari lib/mediaType.js (movie|series).
 */
import React, { useMemo, useState } from "react";
import { ArrowRight, BookmarkPlus, Play, Star } from "lucide-react";

import { moviesApi } from "../../api/index.js";
import Poster from "../../components/movie/Poster.jsx";
import { EmptyState, ErrorState, SkeletonGrid } from "../../components/ui/States.jsx";
import { useAsyncData, useDebounced } from "../../hooks/useAsyncData.js";
import { formatRating, formatYear, joinGenres } from "../../lib/format.js";
import { MEDIA_TYPE, mediaTypeLabel, mediaTypeQuery } from "../../lib/mediaType.js";

function releaseTime(item) {
  return Number(item?.release_year) || 0;
}

function Rail({ title, note, items, onOpen, onAdd, onSeeAll }) {
  if (!items.length) return null;
  return (
    <section className="stream-shelf">
      <div className="stream-shelf-heading">
        <div>
          <h2>{title}</h2>
          <p>{note}</p>
        </div>
        {onSeeAll ? (
          <button type="button" onClick={onSeeAll}>
            Lihat semua <ArrowRight size={14} aria-hidden="true" />
          </button>
        ) : null}
      </div>
      <div className="stream-rail">
        {items.slice(0, 12).map((item) => (
          <article className="stream-card" key={item.id}>
            <button type="button" className="stream-poster" onClick={() => onOpen(item)} aria-label={`Buka ${item.title}`}>
              {item.poster_url ? (
                <img src={item.poster_url} alt="" loading="lazy" />
              ) : (
                <div className="stream-poster-fallback">
                  <span>{item.title?.slice(0, 1) || "?"}</span>
                  <b>{item.title}</b>
                </div>
              )}
              <span className="stream-rating">
                <Star size={12} fill="currentColor" aria-hidden="true" /> {formatRating(item.rating)}
              </span>
              <span className="stream-hover-action">
                <Play size={15} fill="currentColor" aria-hidden="true" />
              </span>
            </button>
            <div className="stream-card-meta">
              <button type="button" onClick={() => onOpen(item)}>
                {item.title}
              </button>
              <span>{formatYear(item.release_year)}</span>
            </div>
            <div className="stream-card-sub">
              <span>{mediaTypeLabel(item.media_type)}</span>
              <span>{joinGenres(item.genre, 2)}</span>
              <button type="button" onClick={() => onAdd(item)} title="Tambah ke watchlist" aria-label={`Tambah ${item.title} ke watchlist`}>
                <BookmarkPlus size={15} aria-hidden="true" />
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default function DiscoverPage({ mediaType, onMediaType, search, onSearch, genre, onGenre, onOpen, onAdd }) {
  const [page] = useState(1);
  const debouncedSearch = useDebounced(search, 350);

  const { data, loading, error, reload } = useAsyncData(
    ({ signal }) =>
      moviesApi.listMovies({
        search: debouncedSearch || undefined,
        genre: genre || undefined,
        mediaType: mediaTypeQuery(mediaType),
        page,
        limit: 60,
        signal,
      }),
    [debouncedSearch, genre, mediaType, page],
  );

  const { items, featured, trending, latest, genres } = useMemo(() => {
    const list = data?.items ?? [];
    const ranked = [...list].sort((a, b) => Number(b.rating || 0) - Number(a.rating || 0));
    const recent = [...list].sort((a, b) => releaseTime(b) - releaseTime(a));
    const chips = [
      ...new Set(
        list
          .flatMap((item) => String(item.genre || "").split(","))
          .map((value) => value.trim())
          .filter(Boolean),
      ),
    ].slice(0, 12);
    return { items: list, featured: ranked[0], trending: ranked, latest: recent, genres: chips };
  }, [data]);

  const total = data?.total ?? 0;

  const isFiltered = Boolean(debouncedSearch || genre);

  return (
    <div className="streaming-home">
      <section className="stream-toolbar">
        <label className="stream-search">
          <span className="search-glyph" aria-hidden="true" />
          <input
            value={search}
            onChange={(event) => onSearch(event.target.value)}
            placeholder="Cari judul film atau series"
            aria-label="Cari judul film atau series"
            type="search"
          />
        </label>
        <div className="stream-format" role="group" aria-label="Jenis tayangan">
          {[MEDIA_TYPE.all, MEDIA_TYPE.movie, MEDIA_TYPE.series].map((value) => (
            <button
              type="button"
              key={value}
              className={mediaType === value ? "chosen" : ""}
              aria-pressed={mediaType === value}
              onClick={() => onMediaType(value)}
            >
              {value === MEDIA_TYPE.all ? "Semua" : mediaTypeLabel(value, { plural: true })}
            </button>
          ))}
        </div>
        <div className="stream-source">
          {loading ? "MEMUAT KATALOG" : `${total} JUDUL DI DATABASE`} <i aria-hidden="true" />
        </div>
      </section>

      {error ? <ErrorState error={error} onRetry={reload} title="Gagal memuat katalog" /> : null}

      {loading && !items.length ? <SkeletonGrid count={12} className="catalog-grid" /> : null}

      {!loading && !error && featured ? (
        <section
          className="feature-hero"
          style={{ "--feature-image": featured.poster_url ? `url("${featured.poster_url}")` : "none" }}
        >
          <div className="feature-backdrop" />
          <div className="feature-copy">
            <div className="feature-kicker">
              <span>SPOTLIGHT</span>
              <i aria-hidden="true" /> {mediaTypeLabel(featured.media_type)} · {formatYear(featured.release_year)}
            </div>
            <h1>{featured.title}</h1>
            <p>{featured.overview || "Belum ada sinopsis untuk judul ini."}</p>
            <div className="feature-data">
              <span>
                <Star size={14} fill="currentColor" aria-hidden="true" /> {formatRating(featured.rating)}
              </span>
              <span>{joinGenres(featured.genre)}</span>
              {featured.director ? <span>{featured.director}</span> : null}
            </div>
            <div className="feature-actions">
              <button type="button" className="feature-primary" onClick={() => onOpen(featured)}>
                <Play size={15} fill="currentColor" aria-hidden="true" /> Lihat detail
              </button>
              <button type="button" className="feature-secondary" onClick={() => onAdd(featured)}>
                <BookmarkPlus size={16} aria-hidden="true" /> Tambah ke watchlist
              </button>
            </div>
          </div>
          <button type="button" className="feature-poster" onClick={() => onOpen(featured)} aria-label={`Buka ${featured.title}`}>
            <Poster item={featured} />
          </button>
          <div className="feature-index">
            <span>01</span>
            <i aria-hidden="true" /> PILIHAN DARI KATALOG
          </div>
        </section>
      ) : null}

      {genres.length ? (
        <section className="genre-section">
          <div className="genre-heading">
            <span>Telusuri genre</span>
            <span>{genre ? `FILTER: ${genre.toUpperCase()}` : "SEMUA GENRE"}</span>
          </div>
          <div className="genre-rail">
            <button type="button" className={!genre ? "genre-chip chosen" : "genre-chip"} onClick={() => onGenre("")}>
              Semua
            </button>
            {genres.map((value, index) => (
              <button
                type="button"
                key={value}
                className={genre === value ? "genre-chip chosen" : "genre-chip"}
                aria-pressed={genre === value}
                onClick={() => onGenre(genre === value ? "" : value)}
              >
                <span>0{index + 1}</span>
                {value}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <Rail
        title="Rating tertinggi"
        note="Judul dengan nilai tertinggi di katalog"
        items={trending}
        onOpen={onOpen}
        onAdd={onAdd}
        onSeeAll={() => onMediaType(MEDIA_TYPE.all)}
      />
      <Rail
        title="Rilis terbaru"
        note="Berdasarkan tahun rilis"
        items={latest}
        onOpen={onOpen}
        onAdd={onAdd}
        onSeeAll={() => onMediaType(MEDIA_TYPE.series)}
      />

      {!loading && !error && !items.length ? (
        <EmptyState
          title={isFiltered ? "Tidak ada judul yang cocok" : "Katalog masih kosong"}
          description={
            isFiltered
              ? "Coba kata kunci lain atau kosongkan filter genre."
              : "Belum ada judul yang tersimpan di database. Admin bisa menambahkannya dari menu Katalog."
          }
          action={
            isFiltered ? (
              <button
                type="button"
                className="text-action"
                onClick={() => {
                  onSearch("");
                  onGenre("");
                  onMediaType(MEDIA_TYPE.all);
                }}
              >
                Bersihkan filter
              </button>
            ) : null
          }
        />
      ) : null}
    </div>
  );
}
