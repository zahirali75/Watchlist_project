import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, ArrowLeft, BookmarkPlus, Clapperboard, Film, LogIn, LogOut, Search, ShieldCheck, Star, Tv, UserRound, X } from "lucide-react";
import { ApiError, api } from "./api.js";
import StreamingHome from "./StreamingHome.jsx";
import "./styles.css";

const initialAuth = () => {
  try { return JSON.parse(sessionStorage.getItem("watchlist-auth") || "null"); } catch { return null; }
};

function App() {
  const [auth, setAuth] = useState(initialAuth);
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState("");
  const [genre, setGenre] = useState("");
  const [kind, setKind] = useState("all");
  const [view, setView] = useState("discover");
  const [selected, setSelected] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [myReviews, setMyReviews] = useState([]);
  const [moderationReviews, setModerationReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dialog, setDialog] = useState("");
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [reviewForm, setReviewForm] = useState({ rating: 8, content: "" });
  const [adminForm, setAdminForm] = useState({ title: "", release_year: new Date().getFullYear(), genre: "Drama", director: "", overview: "", poster_url: "", rating: 0, media_type: "movie", tmdb_id: null, release_date: null, genres: [], poster_path: null });
  const [editingTitle, setEditingTitle] = useState(null);
  const [editingReview, setEditingReview] = useState(null);

  function acceptAuth(payload) {
    const next = { accessToken: payload.accessToken, userId: payload.userId, email: payload.email, name: payload.name, role: payload.role };
    sessionStorage.setItem("watchlist-auth", JSON.stringify(next));
    setAuth(next);
    setDialog("");
  }
  function signOut() {
    sessionStorage.removeItem("watchlist-auth");
    setAuth(null);
    setView("discover");
  }
  async function loadCatalog() {
    setLoading(true); setError("");
    try {
      const result = await api("/movies", { query: { search: query, genre, media_type: kind, limit: 50 } });
      setItems(result.data || []);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }
  async function loadWatchlist() {
    if (!auth) return;
    setLoading(true); setError("");
    try { setWatchlist((await api("/watchlists/me", { token: auth.accessToken, query: { limit: 100 } })).data || []); }
    catch (e) { handleError(e); } finally { setLoading(false); }
  }
  async function loadMyReviews() {
    if (!auth) return;
    setLoading(true); setError("");
    try { setMyReviews((await api("/reviews/me", { token: auth.accessToken, query: { limit: 100 } })).data || []); }
    catch (e) { handleError(e); } finally { setLoading(false); }
  }
  async function loadModerationReviews() {
    if (!auth) return;
    setLoading(true); setError("");
    try { setModerationReviews((await api("/reviews/moderation", { token: auth.accessToken, query: { limit: 100 } })).data || []); }
    catch (e) { handleError(e); } finally { setLoading(false); }
  }
  function handleError(e) {
    if (e instanceof ApiError && e.status === 401 && auth) signOut();
    setError(e.message || "Something went wrong");
  }
  useEffect(() => { if (view === "discover" || view === "admin") loadCatalog(); }, [query, genre, kind, view]);
  useEffect(() => { if (view === "watchlist") loadWatchlist(); if (view === "my-reviews") loadMyReviews(); if (view === "moderation") loadModerationReviews(); }, [view, auth]);
  useEffect(() => {
    if (!selected) return;
    api(`/reviews/movie/${selected.id}`, { query: { limit: 100 } }).then(data => setReviews(data.data || [])).catch(e => setError(e.message));
  }, [selected]);

  async function submitAuth(event) {
    event.preventDefault(); setError("");
    try {
      const payload = dialog === "register" ? await api("/auth/register", { method: "POST", body: form }) : await api("/auth/login", { method: "POST", body: { email: form.email, password: form.password } });
      acceptAuth(payload);
    } catch (e) { setError(e.message); }
  }
  async function addWatch(item) {
    if (!auth) return setDialog("login");
    try { await api("/watchlists", { method: "POST", token: auth.accessToken, body: { movie_id: item.id, status: "want_to_watch" } }); setError(""); }
    catch (e) { handleError(e); }
  }
  async function removeWatch(id) {
    try { await api(`/watchlists/${id}`, { method: "DELETE", token: auth.accessToken }); await loadWatchlist(); }
    catch (e) { handleError(e); }
  }
  async function changeStatus(id, status) {
    try { await api(`/watchlists/${id}`, { method: "PUT", token: auth.accessToken, body: { status } }); await loadWatchlist(); }
    catch (e) { handleError(e); }
  }
  async function submitReview(event) {
    event.preventDefault();
    if (!auth) return setDialog("login");
    try {
      await api("/reviews", { method: "POST", token: auth.accessToken, body: { movie_id: selected.id, rating: Number(reviewForm.rating), content: reviewForm.content } });
      setReviewForm({ rating: 8, content: "" });
      const result = await api(`/reviews/movie/${selected.id}`);
      setReviews(result.data || []);
    } catch (e) { handleError(e); }
  }
  async function removeReview(id) {
    try { await api(`/reviews/${id}`, { method: "DELETE", token: auth.accessToken }); if (view === "moderation") await loadModerationReviews(); else await loadMyReviews(); if (selected) setReviews((await api(`/reviews/movie/${selected.id}`)).data || []); }
    catch (e) { handleError(e); }
  }
  async function moderate(id, is_hidden) {
    try { await api(`/reviews/${id}/moderation`, { method: "PATCH", token: auth.accessToken, body: { is_hidden } }); if (view === "moderation") await loadModerationReviews(); else await loadMyReviews(); }
    catch (e) { handleError(e); }
  }
  async function saveCatalog(event) {
    event.preventDefault(); setError("");
    try {
      await api(editingTitle ? `/movies/${editingTitle}` : "/movies", { method: editingTitle ? "PUT" : "POST", token: auth.accessToken, body: { ...adminForm, release_year: Number(adminForm.release_year), rating: Number(adminForm.rating) } });
      setEditingTitle(null);
      setAdminForm({ title: "", release_year: new Date().getFullYear(), genre: "Drama", director: "", overview: "", poster_url: "", rating: 0, media_type: "movie", tmdb_id: null, release_date: null, genres: [], poster_path: null });
      await loadCatalog();
    } catch (e) { handleError(e); }
  }
  async function deleteCatalog(id) {
    try { await api(`/movies/${id}`, { method: "DELETE", token: auth.accessToken }); setItems(items.filter(item => item.id !== id)); }
    catch (e) { handleError(e); }
  }
  function startCatalogEdit(item) {
    setEditingTitle(item.id);
    setAdminForm({ title: item.title, release_year: item.release_year || new Date().getFullYear(), genre: item.genre || "Drama", director: item.director || "", overview: item.overview || "", poster_url: item.poster_url || "", rating: Number(item.rating || 0), media_type: item.media_type || "movie", tmdb_id: item.tmdb_id ?? null, release_date: item.release_date || null, genres: item.genres || [], poster_path: item.poster_path || null });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  async function saveReviewEdit(event) {
    event.preventDefault();
    try {
      await api(`/reviews/${editingReview.id}`, { method: "PUT", token: auth.accessToken, body: { rating: Number(editingReview.rating), content: editingReview.content } });
      setEditingReview(null);
      await loadMyReviews();
    } catch (e) { handleError(e); }
  }

  const title = view === "watchlist" ? "Your watchlist" : view === "my-reviews" ? "Your reviews" : view === "moderation" ? "Review moderation" : view === "admin" ? "Catalog desk" : "Find your next favorite";
  return <div className="app-shell">
    <header className="topbar">
      <button className="brand" onClick={() => { setView("discover"); setSelected(null); }} aria-label="Reel Index home"><span className="brand-mark"><Clapperboard size={19} /></span><span>REEL<span className="brand-light">INDEX</span></span></button>
      <nav className="main-nav" aria-label="Main navigation">
        <button className={view === "discover" && kind === "all" ? "active" : ""} onClick={() => { setSelected(null); setKind("all"); setView("discover"); }}>Discover</button>
        <button className={view === "discover" && kind === "movie" ? "active" : ""} onClick={() => { setSelected(null); setKind("movie"); setView("discover"); }}>Movies</button>
        <button className={view === "discover" && kind === "tv" ? "active" : ""} onClick={() => { setSelected(null); setKind("tv"); setView("discover"); }}>Series</button>
        {auth && <><button className={view === "watchlist" ? "active" : ""} onClick={() => { setSelected(null); setView("watchlist"); }}>My List</button><button className={view === "my-reviews" ? "active" : ""} onClick={() => { setSelected(null); setView("my-reviews"); }}>Reviews</button></>}
        {auth?.role === "admin" && <><button className={view === "admin" ? "active" : ""} onClick={() => { setSelected(null); setView("admin"); }}>Admin</button><button className={view === "moderation" ? "active" : ""} onClick={() => { setSelected(null); setView("moderation"); }}>Moderation</button></>}
      </nav>
      <div className="account-actions">{auth ? <><span className="account-name"><UserRound size={15} />{auth.name || auth.email.split("@")[0]}</span><button className="login-button" title="Sign out" onClick={signOut}><LogOut size={16} /><span>Logout</span></button></> : <><button className="register-button" onClick={() => setDialog("register")}>Register</button><button className="login-button" onClick={() => setDialog("login")}><LogIn size={16} /><span>Login</span></button></>}</div>
    </header>

    <main>
      {selected ? <Detail item={selected} reviews={reviews} auth={auth} reviewForm={reviewForm} setReviewForm={setReviewForm} submitReview={submitReview} addWatch={addWatch} onBack={() => setSelected(null)} /> : <>
        {view !== "discover" && <section className="page-heading">
          <div className="heading-copy"><div className="eyebrow"><span className="eyebrow-line" /> THE SCREENING ROOM <span className="eyebrow-dot">/</span> 01</div><h1>{title}<span className="title-period">.</span></h1><p>{view === "discover" ? "A considered collection of stories worth your time." : view === "admin" ? "Curate titles in the shared catalog." : "Keep your stories and opinions in one place."}</p></div>
          <div className="heading-stamp"><span>ISSUE</span><strong>NO. 04</strong><small>EST. 2026</small></div>
        </section>}
        {view === "admin" && auth?.role === "admin" && <form className="admin-form" onSubmit={saveCatalog}><div className="form-title"><ShieldCheck size={17} /> {editingTitle ? `EDIT TITLE #${editingTitle}` : "ADD TO CATALOG"}</div><div className="admin-grid"><input required maxLength="255" placeholder="Title" value={adminForm.title} onChange={e => setAdminForm({ ...adminForm, title: e.target.value })} /><select value={adminForm.media_type} onChange={e => setAdminForm({ ...adminForm, media_type: e.target.value })}><option value="movie">Film</option><option value="tv">Series</option></select><input required type="number" min="1888" max="2100" placeholder="Year" value={adminForm.release_year} onChange={e => setAdminForm({ ...adminForm, release_year: e.target.value })} /><input required placeholder="Genre" value={adminForm.genre} onChange={e => setAdminForm({ ...adminForm, genre: e.target.value })} /><input placeholder="Poster URL" value={adminForm.poster_url} onChange={e => setAdminForm({ ...adminForm, poster_url: e.target.value })} /><input type="number" min="0" max="10" step="0.1" placeholder="Rating" value={adminForm.rating} onChange={e => setAdminForm({ ...adminForm, rating: e.target.value })} /></div><textarea maxLength="10000" placeholder="Overview" value={adminForm.overview} onChange={e => setAdminForm({ ...adminForm, overview: e.target.value })} /><div className="admin-form-actions"><button className="primary-button" type="submit">{editingTitle ? "Save changes" : "Add title"}</button>{editingTitle && <button className="text-action" type="button" onClick={() => { setEditingTitle(null); setAdminForm({ title: "", release_year: new Date().getFullYear(), genre: "Drama", director: "", overview: "", poster_url: "", rating: 0, media_type: "movie", tmdb_id: null, release_date: null, genres: [], poster_path: null }); }}>Cancel</button>}</div></form>}
        {error && <div className="notice" role="alert"><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss"><X size={15} /></button></div>}
        {loading ? <div className="loading-state"><Activity size={18} /> Loading catalog from FastAPI…</div> : view === "discover" ? <StreamingHome items={items} search={query} setSearch={setQuery} genre={genre} setGenre={setGenre} onSelect={setSelected} onAdd={addWatch} onMovies={() => { setKind("movie"); setQuery(""); setGenre(""); }} onSeries={() => { setKind("tv"); setQuery(""); setGenre(""); }} /> : view === "watchlist" ? <Watchlist items={watchlist} onStatus={changeStatus} onRemove={removeWatch} onSelect={setSelected} /> : view === "my-reviews" ? <MyReviews items={myReviews} onRemove={removeReview} onEdit={setEditingReview} /> : view === "moderation" ? <MyReviews items={moderationReviews} admin onRemove={removeReview} onModerate={moderate} /> : <Catalog items={items} admin={view === "admin"} onSelect={setSelected} onAdd={addWatch} onDelete={deleteCatalog} onEdit={startCatalogEdit} />}
      </>}
    </main>
    <footer><span>REEL INDEX <i>·</i> THE MOVING IMAGE CATALOG</span><span>DATA SERVED BY WATCHLIST API</span></footer>
    {dialog && <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) { setDialog(""); setError(""); } }}><section className="auth-modal" role="dialog" aria-modal="true" aria-labelledby="auth-title"><button className="modal-close icon-button" onClick={() => setDialog("")} aria-label="Close"><X size={18} /></button><div className="eyebrow">MEMBER ACCESS</div><h2 id="auth-title">{dialog === "register" ? "Create your account" : "Welcome back"}<span className="title-period">.</span></h2><form onSubmit={submitAuth}>{dialog === "register" && <label>Your name<input maxLength="255" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>}<label>Email address<input required type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label><label>Password<input required minLength="8" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label>{error && <p className="form-error">{error}</p>}<button className="primary-button" type="submit">{dialog === "register" ? "Create account" : "Sign in"}</button></form><p className="switch-auth">{dialog === "register" ? "Already registered?" : "New to Reel Index?"} <button onClick={() => { setError(""); setDialog(dialog === "register" ? "login" : "register"); }}> {dialog === "register" ? "Sign in" : "Create account"}</button></p></section></div>}
    {editingReview && <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) setEditingReview(null); }}><section className="auth-modal" role="dialog" aria-modal="true" aria-labelledby="edit-review-title"><button className="modal-close icon-button" onClick={() => setEditingReview(null)} aria-label="Close"><X size={18} /></button><div className="eyebrow">YOUR REVIEW</div><h2 id="edit-review-title">Edit your note<span className="title-period">.</span></h2><form onSubmit={saveReviewEdit}><label>Rating<input required type="number" min="0" max="10" step="0.5" value={editingReview.rating} onChange={e => setEditingReview({ ...editingReview, rating: e.target.value })} /></label><label>Review<textarea required minLength="1" maxLength="5000" value={editingReview.content} onChange={e => setEditingReview({ ...editingReview, content: e.target.value })} /></label>{error && <p className="form-error">{error}</p>}<button className="primary-button" type="submit">Save review</button></form></section></div>}
  </div>;
}

function Catalog({ items, admin, onSelect, onAdd, onDelete, onEdit }) {
  if (!items.length) return <div className="empty-state"><Clapperboard size={24} /><h2>No titles found</h2><p>Try a different title or genre.</p></div>;
  return <section className="catalog-grid">{items.map((item, index) => <article className="title-card" key={item.id} style={{ "--card-index": index }}><button className="poster-button" onClick={() => onSelect(item)} aria-label={`View ${item.title}`}><Poster item={item} /><span className="poster-open">OPEN FILE <ArrowLeft size={13} /></span></button><div className="card-meta"><div><span className="type-label">{item.media_type === "tv" ? "SERIES" : "FILM"}</span><span className="card-year">{item.release_year || "—"}</span></div><span className="score"><Star size={13} fill="currentColor" />{Number(item.rating || 0).toFixed(1)}</span></div><button className="card-title" onClick={() => onSelect(item)}>{item.title}</button><p className="card-genre">{item.genre || (item.genres || []).join(" · ") || "Unclassified"}</p><div className="card-actions">{admin ? <><button className="text-action" onClick={() => onEdit(item)}>Edit</button><button className="text-action danger" onClick={() => onDelete(item.id)}>Remove</button></> : <button className="text-action" onClick={() => onAdd(item)}><BookmarkPlus size={14} /> Add to watchlist</button>}<span>#{String(item.id).padStart(3, "0")}</span></div></article>)}</section>;
}
function Poster({ item }) { return item.poster_url ? <img src={item.poster_url} alt={`${item.title} poster`} loading="lazy" /> : <div className="poster-fallback"><span>{item.media_type === "tv" ? <Tv size={34} /> : <Film size={34} />}</span><b>{item.title}</b><small>{item.release_year || "UNKNOWN YEAR"}</small></div>; }
function Detail({ item, reviews, auth, reviewForm, setReviewForm, submitReview, addWatch, onBack }) {
  return <section className="detail-view"><button className="back-link" onClick={onBack}><ArrowLeft size={16} /> BACK TO CATALOG</button><div className="detail-main"><div className="detail-poster"><Poster item={item} /></div><div className="detail-copy"><div className="eyebrow">{item.media_type === "tv" ? "SERIES FILE" : "FEATURE FILE"} <span className="eyebrow-dot">/</span> {item.release_year || "DATE UNKNOWN"}</div><h1>{item.title}<span className="title-period">.</span></h1><div className="detail-facts"><span><Star size={15} fill="currentColor" /> {Number(item.rating || 0).toFixed(1)} TMDB</span><span>{item.genre || (item.genres || []).join(" · ") || "Genre unlisted"}</span></div><p className="overview">{item.overview || "No synopsis is available for this title."}</p><button className="primary-button add-detail" onClick={() => addWatch(item)}><BookmarkPlus size={16} /> Add to watchlist</button></div></div><section className="reviews-section"><div className="section-bar"><div><div className="eyebrow">THE AUDIENCE <span className="eyebrow-dot">/</span> NOTES</div><h2>Reviews <span>{reviews.length.toString().padStart(2, "0")}</span></h2></div></div><div className="review-layout"><div className="review-list">{reviews.length ? reviews.map(review => <article className="review-entry" key={review.id}><div className="review-byline"><strong>{review.user_name}</strong><span><Star size={13} fill="currentColor" /> {Number(review.rating).toFixed(1)}</span></div><p>{review.content}</p><small>{new Date(review.created_at).toLocaleDateString()}</small></article>) : <div className="empty-review">No public reviews yet. Start the conversation.</div>}</div><form className="review-form" onSubmit={submitReview}><div className="form-title">WRITE A REVIEW</div><label>YOUR RATING <span className="rating-control"><input type="number" min="0" max="10" step="0.5" value={reviewForm.rating} onChange={e => setReviewForm({ ...reviewForm, rating: e.target.value })} /><span>/ 10</span></span></label><textarea required minLength="1" maxLength="5000" placeholder="What did you think?" value={reviewForm.content} onChange={e => setReviewForm({ ...reviewForm, content: e.target.value })} /><button className="primary-button" type="submit">Publish review</button>{!auth && <small>Sign in is required to publish.</small>}</form></div></section></section>;
}
function Watchlist({ items, onStatus, onRemove, onSelect }) {
  if (!items.length) return <div className="empty-state"><BookmarkPlus size={24} /><h2>Your list is waiting</h2><p>Add titles from Discover to keep them close.</p></div>;
  return <section className="list-table"><div className="table-head"><span>TITLE</span><span>TYPE / YEAR</span><span>STATUS</span><span>ACTION</span></div>{items.map(row => <article className="list-row" key={row.id}><button className="list-title" onClick={() => onSelect(row.movies)}><Poster item={row.movies} /><span>{row.movies.title}<small>{row.movies.genre}</small></span></button><span className="list-muted">{row.movies.media_type === "tv" ? "Series" : "Film"} · {row.movies.release_year || "—"}</span><select value={row.status} onChange={e => onStatus(row.id, e.target.value)} aria-label={`Status for ${row.movies.title}`}><option value="want_to_watch">Want to watch</option><option value="watching">Watching</option><option value="watched">Watched</option></select><button className="text-action danger" onClick={() => onRemove(row.id)}>Remove</button></article>)}</section>;
}
function MyReviews({ items, admin, onRemove, onModerate, onEdit, onSelect }) {
  if (!items.length) return <div className="empty-state"><Star size={24} /><h2>No reviews yet</h2><p>Open a title to share your take.</p></div>;
  return <section className="my-review-list">{items.map(review => <article className="my-review" key={review.id}><div className="review-byline">{onSelect ? <button className="review-title-link" onClick={() => onSelect({ id: review.movie_id, title: review.movie_title || `Title #${review.movie_id}` })}>{review.movie_title || `TITLE #${review.movie_id}`}</button> : <span className="review-title-link">TITLE #{review.movie_id}</span>}<span><Star size={13} fill="currentColor" /> {Number(review.rating).toFixed(1)}</span></div><p>{review.content}</p><div className="review-tools"><small>{review.is_hidden ? "Hidden from public" : "Public"}</small>{admin && <button className="text-action" onClick={() => onModerate(review.id, !review.is_hidden)}>{review.is_hidden ? "Restore" : "Hide"}</button>}{onEdit && <button className="text-action" onClick={() => onEdit({ id: review.id, rating: Number(review.rating), content: review.content })}>Edit</button>}<button className="text-action danger" onClick={() => onRemove(review.id)}>Delete</button></div></article>)}</section>;
}

createRoot(document.getElementById("root")).render(<React.StrictMode><App /></React.StrictMode>);
