/**
 * Hero film unggulan. Slide = film rating tertinggi dari API. Backend tidak
 * menyimpan backdrop, durasi, atau URL trailer, jadi poster dipakai sebagai
 * artwork (latar buram + poster tajam di kanan) dan tombol Watch Trailer / durasi
 * tidak ditampilkan.
 */
import React, { useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, Plus, Star } from "lucide-react";

import { formatRating, formatYear, joinGenres } from "../../lib/format.js";

export default function HeroBanner({ items, onOpen, onAdd }) {
  const [index, setIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const count = items.length;
  const movie = items[index % count];

  const step = (delta) => setIndex((current) => (current + delta + count) % count);

  async function add() {
    setBusy(true);
    try {
      await onAdd(movie);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="hero" aria-roledescription="carousel" aria-label="Featured movies">
      <div
        className="hero-art"
        key={movie.id}
        style={movie.poster_url ? { backgroundImage: `url("${movie.poster_url}")` } : undefined}
      />
      {movie.poster_url ? (
        <img className="hero-poster" key={`poster-${movie.id}`} src={movie.poster_url} alt={`Poster ${movie.title}`} />
      ) : null}
      <div className="hero-shade" />

      <div className="hero-copy" key={`copy-${movie.id}`}>
        <span className="hero-label">Featured Movie</span>
        <h1>{movie.title}</h1>
        <p>{movie.overview || "No synopsis available for this title yet."}</p>
        <div className="hero-meta">
          <span className="hero-rating">
            <Star size={16} fill="currentColor" aria-hidden="true" /> {formatRating(movie.rating)}/10
          </span>
          <span>
            <CalendarDays size={15} aria-hidden="true" /> {formatYear(movie.release_year)}
          </span>
          <span>{joinGenres(movie.genre)}</span>
        </div>
        <div className="hero-actions">
          <button type="button" className="btn btn-gold" onClick={() => onOpen(movie)}>
            View Details
          </button>
          <button type="button" className="btn btn-outline" onClick={add} disabled={busy}>
            <Plus size={16} aria-hidden="true" /> {busy ? "Adding…" : "Add to Watchlist"}
          </button>
        </div>
      </div>

      {count > 1 ? (
        <>
          <button type="button" className="hero-nav prev" onClick={() => step(-1)} aria-label="Previous movie">
            <ChevronLeft size={22} aria-hidden="true" />
          </button>
          <button type="button" className="hero-nav next" onClick={() => step(1)} aria-label="Next movie">
            <ChevronRight size={22} aria-hidden="true" />
          </button>
          <div className="hero-dots" role="tablist" aria-label="Choose featured movie">
            {items.map((item, position) => (
              <button
                type="button"
                role="tab"
                key={item.id}
                className={position === index % count ? "active" : ""}
                aria-selected={position === index % count}
                aria-label={`Show ${item.title}`}
                onClick={() => setIndex(position)}
              />
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}
