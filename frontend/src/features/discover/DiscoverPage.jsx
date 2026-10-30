/**
 * Halaman Movies (katalog + hasil pencarian). Semua filter dikirim ke
 * GET /movies (search, genre, media_type, sort, page) — tidak ada penyaringan
 * statis di browser. Kata kunci berasal dari kolom pencarian di header.
 */
import React, { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, SearchX, X } from "lucide-react";

import { moviesApi } from "../../api/index.js";
import MovieTile from "../../components/movie/MovieTile.jsx";
import { EmptyState, ErrorState } from "../../components/ui/States.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { loadGenreCards } from "../../lib/genres.js";
import { MEDIA_TYPE, MEDIA_TYPE_FILTERS, mediaTypeQuery } from "../../lib/mediaType.js";

const PAGE_SIZE = 20;
const SORTS = [
  { value: "id", label: "Default" },
  { value: "rating_desc", label: "Top rated" },
  { value: "year_desc", label: "Newest" },
];

export default function DiscoverPage({
  mediaType,
  onMediaType,
  search,
  onSearch,
  genre,
  onGenre,
  sort,
  onSort,
  onOpen,
  onAdd,
}) {
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [search, genre, mediaType, sort]);

  const catalog = useAsyncData(
    ({ signal }) =>
      moviesApi.listMovies({
        search: search || undefined,
        genre: genre || undefined,
        mediaType: mediaTypeQuery(mediaType),
        sort: sort && sort !== "id" ? sort : undefined,
        page,
        limit: PAGE_SIZE,
        signal,
      }),
    [search, genre, mediaType, sort, page],
  );
  const genres = useAsyncData(({ signal }) => loadGenreCards(10, signal), []);

  const items = catalog.data?.items ?? [];
  const total = catalog.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const filtered = Boolean(search || genre || mediaType !== MEDIA_TYPE.all);

  function reset() {
    onSearch("");
    onGenre("");
    onMediaType(MEDIA_TYPE.all);
    onSort("id");
  }

  return (
    <div className="movies-page">
      <section className="page-heading">
        <h1>{search ? `Results for “${search}”` : genre ? genre : "Movies"}</h1>
        <p>{catalog.loading ? "Loading…" : `${total} ${total === 1 ? "title" : "titles"} found`}</p>
      </section>

      <div className="filter-bar">
        <div className="chips" role="group" aria-label="Media type">
          {MEDIA_TYPE_FILTERS.map(({ value, label }) => (
            <button
              type="button"
              key={value}
              className={mediaType === value ? "active" : ""}
              aria-pressed={mediaType === value}
              onClick={() => onMediaType(value)}
            >
              {label}
            </button>
          ))}
        </div>
        <label className="sort-select">
          <span>Sort by</span>
          <select value={sort || "id"} onChange={(event) => onSort(event.target.value)}>
            {SORTS.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {genres.data?.length ? (
        <div className="chips genre-chips" role="group" aria-label="Genre">
          <button type="button" className={!genre ? "active" : ""} aria-pressed={!genre} onClick={() => onGenre("")}>
            All genres
          </button>
          {genres.data.map(({ name }) => (
            <button
              type="button"
              key={name}
              className={genre === name ? "active" : ""}
              aria-pressed={genre === name}
              onClick={() => onGenre(genre === name ? "" : name)}
            >
              {name}
            </button>
          ))}
        </div>
      ) : null}

      {filtered ? (
        <button type="button" className="clear-filters" onClick={reset}>
          <X size={14} aria-hidden="true" /> Clear filters
        </button>
      ) : null}

      {catalog.error ? <ErrorState error={catalog.error} onRetry={catalog.reload} title="Couldn't load movies" /> : null}

      {!catalog.error && catalog.loading && !items.length ? (
        <div className="tile-grid" aria-hidden="true">
          {Array.from({ length: 10 }, (_, i) => (
            <div className="skeleton-block tile-skeleton" key={i} />
          ))}
        </div>
      ) : null}

      {!catalog.error && !catalog.loading && !items.length ? (
        <EmptyState
          icon={SearchX}
          title={filtered ? "No movies match" : "The catalog is empty"}
          description={filtered ? "Try another title or clear the filters." : "An admin can add movies from the Catalog Admin page."}
          action={
            filtered ? (
              <button type="button" className="btn btn-gold btn-sm" onClick={reset}>
                Clear filters
              </button>
            ) : null
          }
        />
      ) : null}

      {items.length ? (
        <div className="tile-grid">
          {items.map((item) => (
            <MovieTile key={item.id} item={item} onOpen={onOpen} onAdd={onAdd} />
          ))}
        </div>
      ) : null}

      {pages > 1 ? (
        <nav className="pagination" aria-label="Pagination">
          <button type="button" className="btn btn-outline btn-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            <ChevronLeft size={16} aria-hidden="true" /> Previous
          </button>
          <span>
            Page {page} of {pages}
          </span>
          <button type="button" className="btn btn-outline btn-sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>
            Next <ChevronRight size={16} aria-hidden="true" />
          </button>
        </nav>
      ) : null}
    </div>
  );
}
