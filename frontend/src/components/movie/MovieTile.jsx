/** Kartu poster (Trending, New Releases, grid Movies): poster terpisah dari metadata. */
import React from "react";
import { Bookmark, Star } from "lucide-react";

import { formatRating, formatYear, genreList } from "../../lib/format.js";
import Poster from "./Poster.jsx";

export default function MovieTile({ item, rank, onOpen, onAdd }) {
  const genres = genreList(item.genre).slice(0, 2);
  return (
    <article className="tile">
      <div className="tile-poster">
        <button type="button" className="tile-open" onClick={() => onOpen(item)} aria-label={`Open ${item.title}`}>
          <Poster item={item} />
        </button>
        <button
          type="button"
          className="tile-save"
          onClick={() => onAdd(item)}
          aria-label={`Add ${item.title} to watchlist`}
        >
          <Bookmark size={14} aria-hidden="true" />
        </button>
        {rank ? (
          <span className="tile-rank" aria-label={`Rank ${rank}`}>
            {rank}
          </span>
        ) : null}
      </div>
      <button type="button" className="tile-title" onClick={() => onOpen(item)} title={item.title}>
        {item.title}
      </button>
      <span className="tile-year">{formatYear(item.release_year)}</span>
      <span className="tile-rating">
        <Star size={13} fill="currentColor" aria-hidden="true" /> {formatRating(item.rating)}
      </span>
      <div className="tile-genres">
        {genres.map((name) => (
          <span key={name}>{name}</span>
        ))}
      </div>
    </article>
  );
}
