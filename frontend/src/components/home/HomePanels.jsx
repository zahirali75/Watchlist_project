/** Panel-panel dashboard Home: Trending, New Releases, My Watchlist, Genres, Summary. */
import React, { useEffect, useRef, useState } from "react";
import { ArrowRight, Bookmark, CalendarDays, Eye, Film, Flame, Hourglass, MoreVertical, Trophy } from "lucide-react";

import { watchlistApi } from "../../api/index.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { useToast } from "../../context/ToastContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { formatYear } from "../../lib/format.js";
import { genreIcon } from "../../lib/genres.js";
import Poster from "../movie/Poster.jsx";
import MovieTile from "../movie/MovieTile.jsx";
import { EmptyState, ErrorState } from "../ui/States.jsx";

export function PanelHeader({ icon: Icon, title, note, onViewAll, small = false }) {
  return (
    <div className={`panel-header${small ? " small" : ""}`}>
      <Icon size={small ? 18 : 30} className="panel-icon" aria-hidden="true" />
      <div>
        <h2>{title}</h2>
        {note ? <p>{note}</p> : null}
      </div>
      {onViewAll ? (
        <button type="button" className="view-all" onClick={onViewAll}>
          View All <ArrowRight size={13} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
}

function TileRow({ query, ranked, onOpen, onAdd }) {
  if (query.error) return <ErrorState error={query.error} onRetry={query.reload} title="Couldn't load movies" />;
  const items = query.data?.items ?? [];
  if (query.loading && !items.length) {
    return (
      <div className="tile-row" aria-hidden="true">
        {Array.from({ length: 5 }, (_, i) => (
          <div className="skeleton-block tile-skeleton" key={i} />
        ))}
      </div>
    );
  }
  if (!items.length) return <EmptyState icon={Film} title="No movies yet" description="The catalog is empty." />;
  return (
    <div className="tile-row">
      {items.map((item, position) => (
        <MovieTile key={item.id} item={item} rank={ranked ? position + 1 : undefined} onOpen={onOpen} onAdd={onAdd} />
      ))}
    </div>
  );
}

export function TrendingSection({ query, onOpen, onAdd, onViewAll }) {
  return (
    <section className="panel" aria-labelledby="trending-title">
      <PanelHeader icon={Flame} title="Trending Now" note="The highest-rated movies in the catalog" onViewAll={onViewAll} />
      <TileRow query={query} ranked onOpen={onOpen} onAdd={onAdd} />
    </section>
  );
}

export function NewReleasesSection({ query, onOpen, onAdd, onViewAll }) {
  return (
    <section className="panel" aria-labelledby="releases-title">
      <PanelHeader icon={CalendarDays} title="New Releases" note="Latest release years in the catalog" onViewAll={onViewAll} />
      <TileRow query={query} onOpen={onOpen} onAdd={onAdd} />
    </section>
  );
}

const STATUS_LABEL = { want_to_watch: "Want to Watch", watching: "Watching", watched: "Watched" };
const FILTERS = [
  { value: "all", label: "All", stat: "total" },
  { value: "want_to_watch", label: "Want to Watch", stat: "wantToWatch" },
  { value: "watching", label: "Watching", stat: "watching" },
  { value: "watched", label: "Watched", stat: "watched" },
];

function RowMenu({ row, onStatus, onRemove, onOpen }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const close = (event) => {
      if (event.type === "keydown" ? event.key === "Escape" : !ref.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <div className="row-menu" ref={ref}>
      <button type="button" aria-label="Actions" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen(!open)}>
        <MoreVertical size={17} aria-hidden="true" />
      </button>
      {open ? (
        <div className="row-menu-list" role="menu">
          <button type="button" role="menuitem" onClick={() => onOpen(row.movies)}>
            View details
          </button>
          {Object.entries(STATUS_LABEL)
            .filter(([value]) => value !== row.status)
            .map(([value, label]) => (
              <button
                type="button"
                role="menuitem"
                key={value}
                onClick={() => {
                  setOpen(false);
                  onStatus(row, value);
                }}
              >
                Mark as {label}
              </button>
            ))}
          <button type="button" role="menuitem" className="danger" onClick={() => onRemove(row)}>
            Remove
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function WatchlistPanel({ stats, refreshKey, onChanged, onOpen, onViewAll, onOpenAuth }) {
  const { isAuthenticated, withAuth } = useAuth();
  const toast = useToast();
  const [filter, setFilter] = useState("all");

  const list = useAsyncData(
    ({ signal }) =>
      withAuth((token) =>
        watchlistApi.listMyWatchlist({ status: filter === "all" ? undefined : filter, limit: 4, token, signal }),
      ),
    [filter, refreshKey, isAuthenticated],
    { enabled: isAuthenticated },
  );

  async function changeStatus(row, status) {
    try {
      await withAuth((token) => watchlistApi.updateWatchlistItem(row.id, { status }, token));
      toast.success(`Marked as ${STATUS_LABEL[status]}.`);
      onChanged();
    } catch (error) {
      toast.error(error.message);
    }
  }

  async function remove(row) {
    try {
      await withAuth((token) => watchlistApi.removeWatchlistItem(row.id, token));
      toast.success("Removed from watchlist.");
      onChanged();
    } catch (error) {
      toast.error(error.message);
    }
  }

  const rows = list.data?.items ?? [];

  return (
    <section className="panel">
      <PanelHeader icon={Bookmark} title="My Watchlist" small onViewAll={onViewAll} />
      {!isAuthenticated ? (
        <EmptyState
          icon={Bookmark}
          title="Sign in to see your watchlist"
          description="Save movies and track what you've watched."
          action={
            <button type="button" className="btn btn-gold btn-sm" onClick={() => onOpenAuth("login")}>
              Login
            </button>
          }
        />
      ) : (
        <>
          <div className="chips" role="group" aria-label="Filter watchlist by status">
            {FILTERS.map(({ value, label, stat }) => (
              <button
                type="button"
                key={value}
                className={filter === value ? "active" : ""}
                aria-pressed={filter === value}
                onClick={() => setFilter(value)}
              >
                {label}
                {stats ? ` (${stats[stat] ?? 0})` : ""}
              </button>
            ))}
          </div>
          {list.error ? <ErrorState error={list.error} onRetry={list.reload} title="Couldn't load watchlist" /> : null}
          {!list.error && list.loading && !rows.length ? <div className="skeleton-block wl-skeleton" aria-hidden="true" /> : null}
          {!list.error && !list.loading && !rows.length ? (
            <EmptyState icon={Bookmark} title="Nothing here yet" description="Add a movie to start your list." />
          ) : null}
          <ul className="wl-list">
            {rows.map((row) => {
              const movie = row.movies || {};
              return (
                <li key={row.id}>
                  <button type="button" className="wl-thumb" onClick={() => onOpen(movie)} aria-label={`Open ${movie.title}`}>
                    <Poster item={movie} />
                  </button>
                  <div className="wl-info">
                    <strong>{movie.title || `Title #${row.movie_id}`}</strong>
                    <span>{formatYear(movie.release_year)}</span>
                  </div>
                  <span className={`status-pill st-${row.status}`}>{STATUS_LABEL[row.status] ?? row.status}</span>
                  <RowMenu row={row} onStatus={changeStatus} onRemove={remove} onOpen={onOpen} />
                </li>
              );
            })}
          </ul>
        </>
      )}
    </section>
  );
}

export function GenreCard({ genre, onClick }) {
  const Icon = genreIcon(genre.name);
  return (
    <button type="button" className="genre-card" onClick={() => onClick(genre.name)}>
      {genre.poster ? <img src={genre.poster} alt="" loading="lazy" /> : null}
      <span className="genre-card-body">
        <Icon size={22} aria-hidden="true" />
        <strong>{genre.name}</strong>
        <small>
          {genre.total} {genre.total === 1 ? "movie" : "movies"}
        </small>
      </span>
    </button>
  );
}

export function GenresPanel({ query, onGenre, onViewAll }) {
  const items = query.data ?? [];
  return (
    <section className="panel">
      <PanelHeader icon={Bookmark} title="Genres" note="Explore by your favorite genre" small onViewAll={onViewAll} />
      {query.error ? <ErrorState error={query.error} onRetry={query.reload} title="Couldn't load genres" /> : null}
      {!query.error && query.loading && !items.length ? <div className="skeleton-block genre-skeleton" aria-hidden="true" /> : null}
      {!query.error && !query.loading && !items.length ? (
        <EmptyState icon={Film} title="No genres yet" description="Genres appear once movies are added." />
      ) : null}
      <div className="genre-row">
        {items.map((genre) => (
          <GenreCard key={genre.name} genre={genre} onClick={onGenre} />
        ))}
      </div>
    </section>
  );
}

export function SummaryPanel({ stats, error, onRetry, onViewAll, onOpenAuth, isAuthenticated }) {
  const cells = [
    { icon: Bookmark, label: "Total Movies", key: "total" },
    { icon: Eye, label: "Watched", key: "watched" },
    { icon: Hourglass, label: "Watching", key: "watching" },
    { icon: Trophy, label: "Want to Watch", key: "wantToWatch" },
  ];
  return (
    <section className="panel">
      <PanelHeader icon={Bookmark} title="Watchlist Summary" small onViewAll={onViewAll} />
      {!isAuthenticated ? (
        <p className="panel-hint">
          <button type="button" className="link-btn" onClick={() => onOpenAuth("login")}>
            Login
          </button>{" "}
          to see your stats.
        </p>
      ) : error ? (
        <ErrorState error={error} onRetry={onRetry} title="Couldn't load stats" />
      ) : (
        <dl className="summary">
          {cells.map(({ icon: Icon, label, key }) => (
            <div key={key}>
              <Icon size={26} aria-hidden="true" />
              <dt>{label}</dt>
              <dd>{stats ? (stats[key] ?? 0) : "—"}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}

