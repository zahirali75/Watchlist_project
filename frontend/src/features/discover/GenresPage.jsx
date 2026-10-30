/** Halaman Genres: kartu genre dengan jumlah judul nyata dari API; klik = filter katalog. */
import React from "react";
import { Film } from "lucide-react";

import { GenreCard } from "../../components/home/HomePanels.jsx";
import { EmptyState, ErrorState } from "../../components/ui/States.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { loadGenreCards } from "../../lib/genres.js";

export default function GenresPage({ onGenre }) {
  const { data, loading, error, reload } = useAsyncData(({ signal }) => loadGenreCards(20, signal), []);
  const items = data ?? [];

  return (
    <div className="genres-page">
      <section className="page-heading">
        <h1>Genres</h1>
        <p>Explore by your favorite genre</p>
      </section>
      {error ? <ErrorState error={error} onRetry={reload} title="Couldn't load genres" /> : null}
      {!error && loading && !items.length ? <div className="skeleton-block genre-skeleton" aria-hidden="true" /> : null}
      {!error && !loading && !items.length ? (
        <EmptyState icon={Film} title="No genres yet" description="Genres appear once movies are added." />
      ) : null}
      <div className="genre-grid">
        {items.map((genre) => (
          <GenreCard key={genre.name} genre={genre} onClick={onGenre} />
        ))}
      </div>
    </div>
  );
}
