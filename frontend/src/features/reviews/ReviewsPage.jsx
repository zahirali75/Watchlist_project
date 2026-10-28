/**
 * Halaman "Ulasan Saya" (GET /reviews/me) dan "Moderasi" (GET /reviews/moderation).
 *
 * Keduanya memakai komponen yang sama karena bentuk datanya identik; yang
 * berbeda hanya izin moderasi dan asal endpoint. Perbedaan ini dulu tersembunyi
 * di dalam satu komponen `MyReviews` dengan prop `admin`.
 */
import React from "react";
import { Star } from "lucide-react";

import { reviewsApi } from "../../api/index.js";
import { EmptyState, ErrorState, LoadingState } from "../../components/ui/States.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useToast } from "../../context/ToastContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { formatDate, formatRating, titleOrFallback } from "../../lib/format.js";

export default function ReviewsPage({ moderation = false, onOpenMovie }) {
  const { withAuth } = useAuth();
  const toast = useToast();

  const { data, loading, error, reload, setData } = useAsyncData(
    () =>
      withAuth((token) =>
        moderation
          ? reviewsApi.listReviewsForModeration({ token, limit: 100 })
          : reviewsApi.listMyReviews({ token, limit: 100 }),
      ),
    [moderation],
  );

  const reviews = data?.items ?? [];

  async function toggleHidden(review) {
    try {
      await withAuth((token) => reviewsApi.moderateReview(review.id, !review.is_hidden, token));
      setData((current) => ({
        ...current,
        items: (current?.items ?? []).map((row) => (row.id === review.id ? { ...row, is_hidden: !review.is_hidden } : row)),
      }));
      toast.success(review.is_hidden ? "Ulasan ditampilkan kembali." : "Ulasan disembunyikan.");
    } catch (caught) {
      toast.error(caught.message);
    }
  }

  async function removeReview(reviewId) {
    if (!window.confirm("Hapus ulasan ini?")) return;
    try {
      await withAuth((token) => reviewsApi.deleteReview(reviewId, token));
      setData((current) => ({ ...current, items: (current?.items ?? []).filter((row) => row.id !== reviewId) }));
      toast.success("Ulasan dihapus.");
    } catch (caught) {
      toast.error(caught.message);
    }
  }

  if (loading) return <LoadingState label="Memuat ulasan…" />;
  if (error) return <ErrorState error={error} onRetry={reload} title="Gagal memuat ulasan" />;

  if (!reviews.length) {
    return (
      <EmptyState
        icon={Star}
        title={moderation ? "Belum ada ulasan untuk dimoderasi" : "Kamu belum menulis ulasan"}
        description={
          moderation
            ? "Semua ulasan pengguna akan muncul di sini, termasuk yang disembunyikan."
            : "Buka halaman detail sebuah judul untuk membagikan pendapatmu."
        }
      />
    );
  }

  return (
    <section className="my-review-list">
      {reviews.map((review) => (
        <article className="my-review" key={review.id}>
          <div className="review-byline">
            <button
              type="button"
              className="review-title-link"
              onClick={() =>
                onOpenMovie({ id: review.movie_id, title: titleOrFallback(review.movie_title, review.movie_id) })
              }
            >
              {titleOrFallback(review.movie_title, review.movie_id).toUpperCase()}
            </button>
            <span>
              <Star size={13} fill="currentColor" aria-hidden="true" /> {formatRating(review.rating)}
            </span>
          </div>
          <p>{review.content}</p>
          <div className="review-tools">
            <small>
              {moderation && review.user_name ? `${review.user_name} · ` : ""}
              {formatDate(review.created_at)} · {review.is_hidden ? "Disembunyikan" : "Tampil publik"}
            </small>
            {moderation ? (
              <button type="button" className="text-action" onClick={() => toggleHidden(review)}>
                {review.is_hidden ? "Tampilkan" : "Sembunyikan"}
              </button>
            ) : null}
            <button type="button" className="text-action danger" onClick={() => removeReview(review.id)}>
              Hapus
            </button>
          </div>
        </article>
      ))}
    </section>
  );
}
