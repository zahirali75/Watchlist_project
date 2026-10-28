/** Kartu film/grid katalog. */
import React from "react";
import { BookmarkPlus, Star } from "lucide-react";

import { formatRating, formatYear, joinGenres, padId } from "../../lib/format.js";
import { mediaTypeLabel } from "../../lib/mediaType.js";
import Poster from "./Poster.jsx";

export default function MovieCard({ item, index = 0, admin = false, onOpen, onAdd, onEdit, onDelete, onRemove }) {
  return (
    <article className="title-card" style={{ "--card-index": index }}>
      <button type="button" className="poster-button" onClick={() => onOpen(item)} aria-label={`Lihat ${item.title}`}>
        <Poster item={item} />
      </button>

      <div className="card-meta">
        <div>
          <span className="type-label">{mediaTypeLabel(item.media_type)}</span>
          <span className="card-year">{formatYear(item.release_year)}</span>
        </div>
        <span className="score">
          <Star size={13} fill="currentColor" aria-hidden="true" />
          {formatRating(item.rating)}
        </span>
      </div>

      <button type="button" className="card-title" onClick={() => onOpen(item)} title={item.title}>
        {item.title}
      </button>
      <p className="card-genre">{joinGenres(item.genre)}</p>

      <div className="card-actions">
        {admin ? (
          <>
            <button type="button" className="text-action" onClick={() => onEdit(item)}>
              Edit
            </button>
            <button type="button" className="text-action danger" onClick={() => onDelete(item)}>
              Hapus
            </button>
          </>
        ) : (
          <button type="button" className="text-action" onClick={() => onAdd(item)}>
            <BookmarkPlus size={14} aria-hidden="true" /> Tambah ke watchlist
          </button>
        )}
        {onRemove ? (
          <button type="button" className="text-action danger" onClick={() => onRemove(item)}>
            Hapus
          </button>
        ) : null}
        <span>#{padId(item.id)}</span>
      </div>
    </article>
  );
}
