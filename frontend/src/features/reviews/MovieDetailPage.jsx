/**
 * Halaman detail film + ulasan.
 *
 * Perbaikan integrasi penting di sini: daftar ulasan (`GET /reviews/movie/{id}`)
 * butuh token di backend, tetapi versi lama memanggilnya tanpa token — jadi
 * halaman ini selalu gagal memuat ulasan (401) bagi pengguna yang sudah masuk,
 * dan menampilkan pesan error. Sekarang pemanggilan memakai `withAuth`.
 */
import React, { useEffect, useState } from "react";
import { ArrowLeft, BookmarkPlus, Star } from "lucide-react";

import { moviesApi, reviewsApi } from "../../api/index.js";
import Poster from "../../components/movie/Poster.jsx";
import { EmptyState, ErrorState, LoadingState } from "../../components/ui/States.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useToast } from "../../context/ToastContext.jsx";
import { formatDate, formatRating, formatYear, joinGenres } from "../../lib/format.js";
import { mediaTypeLabel } from "../../lib/mediaType.js";

export default function MovieDetailPage({ movieId, onBack, onAdd, onRequireAuth }) {
  const { isAuthenticated, user, withAuth } = useAuth();
  const toast = useToast();

  const [movie, setMovie] = useState(null);
  const [movieError, setMovieError] = useState(null);
  const [movieLoading, setMovieLoading] = useState(true);

  const [reviews, setReviews] = useState([]);
  const [reviewsError, setReviewsError] = useState(null);
  const [reviewsLoading, setReviewsLoading] = useState(false);

  const [form, setForm] = useState({ rating: 8, content: "" });
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setMovieLoading(true);
    setMovieError(null);
    moviesApi
      .getMovie(movieId, { signal: controller.signal })
      .then(setMovie)
      .catch((error) => {
        if (error?.name !== "AbortError") setMovieError(error);
      })
      .finally(() => {
        if (!controller.signal.aborted) setMovieLoading(false);
      });
    return () => controller.abort();
  }, [movieId]);

  async function loadReviews() {
    if (!isAuthenticated) {
      setReviews([]);
      return;
    }
    setReviewsLoading(true);
    setReviewsError(null);
    try {
      const result = await withAuth((token) => reviewsApi.listMovieReviews(movieId, { token, limit: 100 }));
      setReviews(result.items);
    } catch (error) {
      setReviewsError(error);
    } finally {
      setReviewsLoading(false);
    }
  }

  useEffect(() => {
    loadReviews();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [movieId, isAuthenticated]);

  const myReview = user ? reviews.find((review) => String(review.user_id) === String(user.userId)) : null;

  async function onSubmitReview(event) {
    event.preventDefault();
    if (!isAuthenticated) {
      onRequireAuth();
      return;
    }
    if (!form.content.trim()) {
      setFormError("Isi ulasan tidak boleh kosong.");
      return;
    }
    const rating = Number(form.rating);
    if (!Number.isFinite(rating) || rating < 0 || rating > 10) {
      setFormError("Rating harus antara 0 dan 10.");
      return;
    }

    setFormError("");
    setSaving(true);
    try {
      await withAuth((token) => reviewsApi.createReview({ movieId, rating, content: form.content.trim() }, token));
      setForm({ rating: 8, content: "" });
      toast.success("Ulasan tersimpan.");
      await loadReviews();
    } catch (error) {
      if (error.status === 409) {
        setFormError("Kamu sudah pernah mengulas film ini. Hapus ulasan lama dulu untuk menulis yang baru.");
      } else {
        setFormError(error.message);
      }
    } finally {
      setSaving(false);
    }
  }

  async function onDeleteReview(reviewId) {
    if (!window.confirm("Hapus ulasan ini?")) return;
    try {
      await withAuth((token) => reviewsApi.deleteReview(reviewId, token));
      toast.success("Ulasan dihapus.");
      await loadReviews();
    } catch (error) {
      toast.error(error.message);
    }
  }

  if (movieLoading) return <LoadingState label="Memuat detail film…" />;
  if (movieError) return <ErrorState error={movieError} title="Gagal memuat film" />;
  if (!movie) return null;

  return (
    <section className="detail-view">
      <button type="button" className="back-link" onClick={onBack}>
        <ArrowLeft size={16} aria-hidden="true" /> KEMBALI
      </button>

      <div className="detail-main">
        <div className="detail-poster">
          <Poster item={movie} />
        </div>
        <div className="detail-copy">
          <div className="eyebrow">
            {mediaTypeLabel(movie.media_type).toUpperCase()} <span className="eyebrow-dot">/</span>{" "}
            {formatYear(movie.release_year)}
          </div>
          <h1>
            {movie.title}
            <span className="title-period">.</span>
          </h1>
          <div className="detail-facts">
            <span>
              <Star size={15} fill="currentColor" aria-hidden="true" /> {formatRating(movie.rating)}
            </span>
            <span>{joinGenres(movie.genre)}</span>
            {movie.director ? <span>Sutradara: {movie.director}</span> : null}
          </div>
          <p className="overview">{movie.overview || "Belum ada sinopsis untuk judul ini."}</p>
          <button type="button" className="primary-button add-detail" onClick={() => onAdd(movie)}>
            <BookmarkPlus size={16} aria-hidden="true" /> Tambah ke watchlist
          </button>
        </div>
      </div>

      <section className="reviews-section">
        <div className="section-bar">
          <div>
            <div className="eyebrow">
              CATATAN PENONTON <span className="eyebrow-dot">/</span> ULASAN
            </div>
            <h2>
              Ulasan <span>{String(reviews.length).padStart(2, "0")}</span>
            </h2>
          </div>
        </div>

        <div className="review-layout">
          <div className="review-list">
            {!isAuthenticated ? (
              <EmptyState
                title="Masuk untuk membaca ulasan"
                description="Backend menutup daftar ulasan untuk pengguna anonim supaya identitas penulis tidak bocor."
                action={
                  <button type="button" className="text-action" onClick={onRequireAuth}>
                    Masuk sekarang
                  </button>
                }
              />
            ) : reviewsLoading ? (
              <LoadingState label="Memuat ulasan…" compact />
            ) : reviewsError ? (
              <ErrorState error={reviewsError} onRetry={loadReviews} title="Gagal memuat ulasan" />
            ) : reviews.length ? (
              reviews.map((review) => (
                <article className="review-entry" key={review.id}>
                  <div className="review-byline">
                    <strong>{review.user_name || "Anggota"}</strong>
                    <span>
                      <Star size={13} fill="currentColor" aria-hidden="true" /> {formatRating(review.rating)}
                    </span>
                  </div>
                  <p>{review.content}</p>
                  <div className="review-tools">
                    <small>{formatDate(review.created_at)}</small>
                    {myReview && review.id === myReview.id ? (
                      <button type="button" className="text-action danger" onClick={() => onDeleteReview(review.id)}>
                        Hapus ulasan saya
                      </button>
                    ) : null}
                  </div>
                </article>
              ))
            ) : (
              <div className="empty-review">Belum ada ulasan publik. Jadilah yang pertama menulis.</div>
            )}
          </div>

          <div>
            {!isAuthenticated ? (
              <div className="review-form">
                <div className="form-title">TULIS ULASAN</div>
                <p className="form-hint">Masuk dulu untuk menulis ulasan.</p>
                <button type="button" className="primary-button" onClick={onRequireAuth}>
                  Masuk
                </button>
              </div>
            ) : myReview ? (
              <div className="review-form">
                <div className="form-title">ULASAN KAMU</div>
                <p className="form-hint">
                  Kamu sudah mengulas film ini ({formatRating(myReview.rating)}). Satu pengguna satu ulasan per film —
                  hapus ulasan lama untuk menulis yang baru.
                </p>
                <button type="button" className="text-action danger" onClick={() => onDeleteReview(myReview.id)}>
                  Hapus ulasan saya
                </button>
              </div>
            ) : (
              <form className="review-form" onSubmit={onSubmitReview}>
                <div className="form-title">TULIS ULASAN</div>
                <label>
                  RATING KAMU
                  <span className="rating-control">
                    <input
                      type="number"
                      min="0"
                      max="10"
                      step="0.5"
                      value={form.rating}
                      onChange={(event) => setForm({ ...form, rating: event.target.value })}
                    />
                    <span>/ 10</span>
                  </span>
                </label>
                <label>
                  ULASAN
                  <textarea
                    required
                    maxLength={5000}
                    value={form.content}
                    onChange={(event) => setForm({ ...form, content: event.target.value })}
                    placeholder="Apa yang membuat judul ini layak ditonton?"
                  />
                </label>
                {formError ? (
                  <p className="form-error" role="alert">
                    {formError}
                  </p>
                ) : null}
                <button className="primary-button" type="submit" disabled={saving}>
                  {saving ? "Menyimpan…" : "Kirim ulasan"}
                </button>
              </form>
            )}
          </div>
        </div>
      </section>
    </section>
  );
}
