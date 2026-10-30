/**
 * Beranda (dashboard). Semua data dari API:
 *   hero + Trending  → GET /movies?sort=rating_desc&limit=5
 *   New Releases     → GET /movies?sort=year_desc&limit=5
 *   Genres           → lib/genres.js (GET /movies?genre=…)
 *   My Watchlist     → GET /watchlists/me (+ PUT/DELETE /watchlists/{id})
 *   Summary          → GET /users/me/stats
 */
import React, { useState } from "react";
import { Film } from "lucide-react";

import { authApi, moviesApi } from "../../api/index.js";
import HeroBanner from "../../components/home/HeroBanner.jsx";
import {
  GenresPanel,
  NewReleasesSection,
  SummaryPanel,
  TrendingSection,
  WatchlistPanel,
} from "../../components/home/HomePanels.jsx";
import { EmptyState, ErrorState } from "../../components/ui/States.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { loadGenreCards } from "../../lib/genres.js";

export default function HomePage({ watchlistVersion, onOpen, onAdd, onViewAll, onGenre, onNavigate, onOpenAuth }) {
  const { isAuthenticated, withAuth } = useAuth();
  const [tick, setTick] = useState(0);
  const refreshKey = `${watchlistVersion}-${tick}`;

  const top = useAsyncData(({ signal }) => moviesApi.listMovies({ sort: "rating_desc", limit: 5, signal }), []);
  const latest = useAsyncData(({ signal }) => moviesApi.listMovies({ sort: "year_desc", limit: 5, signal }), []);
  const genres = useAsyncData(({ signal }) => loadGenreCards(5, signal), []);
  const stats = useAsyncData(
    () => withAuth((token) => authApi.getMyStats(token)),
    [refreshKey, isAuthenticated],
    { enabled: isAuthenticated },
  );

  const heroItems = top.data?.items ?? [];

  return (
    <div className="home">
      {top.error ? (
        <ErrorState error={top.error} onRetry={top.reload} title="Couldn't load featured movies" />
      ) : heroItems.length ? (
        <HeroBanner items={heroItems} onOpen={onOpen} onAdd={onAdd} />
      ) : top.loading ? (
        <div className="hero hero-skeleton skeleton-block" aria-hidden="true" />
      ) : (
        <EmptyState icon={Film} title="The catalog is empty" description="Movies will appear here once an admin adds them." />
      )}

      <div className="home-grid">
        <div className="home-col">
          <TrendingSection query={top} onOpen={onOpen} onAdd={onAdd} onViewAll={() => onViewAll("rating_desc")} />
          <NewReleasesSection query={latest} onOpen={onOpen} onAdd={onAdd} onViewAll={() => onViewAll("year_desc")} />
        </div>
        <div className="home-col">
          <WatchlistPanel
            stats={stats.data}
            refreshKey={refreshKey}
            onChanged={() => setTick((value) => value + 1)}
            onOpen={onOpen}
            onViewAll={() => onNavigate({ view: "watchlist" })}
            onOpenAuth={onOpenAuth}
          />
          <GenresPanel query={genres} onGenre={onGenre} onViewAll={() => onNavigate({ view: "genres" })} />
          <SummaryPanel
            stats={stats.data}
            error={stats.error}
            onRetry={stats.reload}
            isAuthenticated={isAuthenticated}
            onViewAll={() => onNavigate({ view: "profile" })}
            onOpenAuth={onOpenAuth}
          />
        </div>
      </div>
    </div>
  );
}
