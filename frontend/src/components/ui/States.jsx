/** Komponen tampilan bersama: state kosong/memuat/gagal, spanduk pesan, pita. */

import React from "react";
import { Activity, AlertTriangle, RotateCcw } from "lucide-react";

/** State memuat dengan teks yang bisa disesuaikan. */
export function LoadingState({ label = "Memuat…", compact = false }) {
  return (
    <div className={compact ? "loading-state loading-state--compact" : "loading-state"} role="status" aria-live="polite">
      <Activity size={18} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

/**
 * State kosong. `action` dipakai untuk memberi jalan keluar (mis. tombol
 * "Muat ulang" saat daftar kosong karena filter).
 */
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="empty-state">
      {Icon ? <Icon size={24} aria-hidden="true" /> : null}
      <h2>{title}</h2>
      {description ? <p>{description}</p> : null}
      {action ?? null}
    </div>
  );
}

/**
 * State gagal. Selalu menampilkan pesan asli dari backend + tombol coba lagi,
 * supaya error bisa dilacak alih-alih disembunyikan.
 */
export function ErrorState({ error, onRetry, title = "Gagal memuat data" }) {
  const message = error?.message || "Terjadi kesalahan yang tidak diketahui.";
  return (
    <div className="error-state" role="alert">
      <AlertTriangle size={22} aria-hidden="true" />
      <h2>{title}</h2>
      <p>{message}</p>
      {error?.status ? <small>HTTP {error.status}{error.code ? ` · ${error.code}` : ""}</small> : null}
      {onRetry ? (
        <button type="button" className="text-action" onClick={onRetry}>
          <RotateCcw size={14} aria-hidden="true" /> Coba lagi
        </button>
      ) : null}
    </div>
  );
}

/** Pita skeleton untuk daftar yang sedang dimuat. */
export function SkeletonGrid({ count = 10, className = "catalog-grid" }) {
  return (
    <div className={className} aria-hidden="true">
      {Array.from({ length: count }, (_, index) => (
        <div className="skeleton-card" key={index}>
          <div className="skeleton-block skeleton-poster" />
          <div className="skeleton-block skeleton-line" />
          <div className="skeleton-block skeleton-line skeleton-line--short" />
        </div>
      ))}
    </div>
  );
}
