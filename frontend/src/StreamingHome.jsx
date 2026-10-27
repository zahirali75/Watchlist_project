import React from "react";
import { ArrowRight, BookmarkPlus, Play, Star } from "lucide-react";

function releaseTime(item) {
  const date = item.release_date ? Date.parse(item.release_date) : Date.parse(`${item.release_year || 0}-01-01`);
  return Number.isNaN(date) ? 0 : date;
}

function PosterCard({ item, onSelect, onAdd }) {
  return <article className="stream-card">
    <button className="stream-poster" onClick={() => onSelect(item)} aria-label={`Open ${item.title}`}>
      {item.poster_url ? <img src={item.poster_url} alt={`${item.title} poster`} loading="lazy" /> : <div className="stream-poster-fallback"><span>{item.title?.slice(0, 1) || "C"}</span><b>{item.title}</b></div>}
      <span className="stream-rating"><Star size={12} fill="currentColor" /> {Number(item.rating || 0).toFixed(1)}</span>
      <span className="stream-hover-action"><Play size={15} fill="currentColor" /></span>
    </button>
    <div className="stream-card-meta"><button onClick={() => onSelect(item)}>{item.title}</button><span>{item.release_year || "—"}</span></div>
    <div className="stream-card-sub"><span>{item.media_type === "tv" ? "SERIES" : "MOVIE"}</span><span>{item.genre || (item.genres || []).slice(0, 2).join(" · ") || "Catalog"}</span><button onClick={() => onAdd(item)} title="Add to watchlist" aria-label={`Add ${item.title} to watchlist`}><BookmarkPlus size={15} /></button></div>
  </article>;
}

function Shelf({ title, note, items, onSelect, onAdd, onSeeAll }) {
  if (!items.length) return null;
  return <section className="stream-shelf">
    <div className="stream-shelf-heading"><div><h2>{title}</h2><p>{note}</p></div><button onClick={onSeeAll}>View all <ArrowRight size={14} /></button></div>
    <div className="stream-rail">{items.slice(0, 12).map(item => <PosterCard key={item.id} item={item} onSelect={onSelect} onAdd={onAdd} />)}</div>
  </section>;
}

export default function StreamingHome({ items, search, setSearch, genre, setGenre, onSelect, onAdd, onMovies, onSeries }) {
  const ranked = [...items].sort((a, b) => Number(b.rating || 0) - Number(a.rating || 0));
  const latest = [...items].sort((a, b) => releaseTime(b) - releaseTime(a));
  const featured = ranked[0];
  const genres = [...new Set(items.flatMap(item => item.genres?.length ? item.genres : (item.genre || "").split(",")).map(value => value.trim()).filter(Boolean))].slice(0, 12);
  const trending = ranked.slice(0, 12);
  const releases = latest.slice(0, 12);

  return <div className="streaming-home">
    <section className="stream-toolbar">
      <label className="stream-search"><span className="search-glyph" /><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search movies and series" aria-label="Search movies and series" /></label>
      <div className="stream-format"><button onClick={onMovies}>Movies</button><button onClick={onSeries}>Series</button></div>
      <div className="stream-source">YOUR DATABASE <i /> LIVE CATALOG</div>
    </section>

    {featured && <section className="feature-hero" style={{ "--feature-image": featured.poster_url ? `url("${featured.poster_url}")` : "none" }}>
      <div className="feature-backdrop" />
      <div className="feature-copy"><div className="feature-kicker"><span>EDITOR'S SPOTLIGHT</span><i /> {featured.media_type === "tv" ? "SERIES" : "FILM"} · {featured.release_year || "—"}</div>
        <h1>{featured.title}</h1><p>{featured.overview || "Discover this title from your Watchlist catalog."}</p>
        <div className="feature-data"><span><Star size={14} fill="currentColor" /> {Number(featured.rating || 0).toFixed(1)} TMDB</span><span>{featured.genre || (featured.genres || []).slice(0, 3).join(" · ")}</span></div>
        <div className="feature-actions"><button className="feature-primary" onClick={() => onSelect(featured)}><Play size={15} fill="currentColor" /> Explore title</button><button className="feature-secondary" onClick={() => onAdd(featured)}><BookmarkPlus size={16} /> My list</button></div>
      </div>
      <button className="feature-poster" onClick={() => onSelect(featured)} aria-label={`Explore ${featured.title}`}>
        {featured.poster_url ? <img src={featured.poster_url} alt={`${featured.title} poster`} /> : <div className="feature-no-poster">{featured.title}</div>}
      </button>
      <div className="feature-index"><span>01</span><i /> FEATURED FROM THE CATALOG</div>
    </section>}

    <section className="genre-section"><div className="genre-heading"><span>Browse by mood</span><span>{genre ? `FILTER: ${genre.toUpperCase()}` : "GENRES"}</span></div><div className="genre-rail"><button className={!genre ? "genre-chip chosen" : "genre-chip"} onClick={() => setGenre("")}>All titles</button>{genres.map((value, index) => <button key={value} className={genre === value ? "genre-chip chosen" : "genre-chip"} onClick={() => setGenre(genre === value ? "" : value)}><span>0{index + 1}</span>{value}</button>)}</div></section>

    <Shelf title="Trending now" note="The highest-rated titles in your catalog" items={trending} onSelect={onSelect} onAdd={onAdd} onSeeAll={onMovies} />
    <Shelf title="New releases" note="Recently released films and series" items={releases} onSelect={onSelect} onAdd={onAdd} onSeeAll={onSeries} />
    {!items.length && <section className="stream-empty"><div className="empty-mark">C</div><h2>Your cinema starts here.</h2><p>No titles came back from the Watchlist API. Check the API connection and import catalog data into the configured PostgreSQL database.</p></section>}
  </div>;
}
