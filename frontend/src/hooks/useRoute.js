/**
 * Navigasi berbasis hash (#/watchlist) tanpa menambah dependensi router.
 *
 * Mengapa diubah: versi lama menyimpan halaman aktif di state React, sehingga
 * tombol Back browser menutup aplikasi, URL tidak bisa dibagikan, dan halaman
 * detail film hilang begitu di-refresh. Hash dipilih (bukan History API) supaya
 * `vite build` tetap bisa dilayani dari file statis mana pun tanpa aturan
 * rewrite server.
 */
import { useCallback, useEffect, useState } from "react";

const ROUTES = new Set([
  "discover",
  "watchlist",
  "my-reviews",
  "moderation",
  "admin",
  "profile",
  "forgot-password",
  "reset-password",
]);

function parseHash() {
  const raw = window.location.hash.replace(/^#\/?/, "");
  const [path, search] = raw.split("?");
  const segments = path.split("/").filter(Boolean);
  const params = new URLSearchParams(search || "");
  return { segments, params };
}

/** Susun hash dari potongan path, mis. buildHash("movie", 42) → "#/movie/42". */
export function buildHash(...parts) {
  const clean = parts.filter((part) => part !== undefined && part !== null && part !== "").join("/");
  return clean ? `#/${clean}` : "#/";
}

export function navigate(...parts) {
  const next = buildHash(...parts);
  if (window.location.hash !== next) window.location.hash = next;
}

/**
 * Rute aktif: { view, movieId, token } — token dipakai halaman reset-password
 * yang menerima token dari email (`#/reset-password?token=...`).
 */
export function useRoute() {
  const [route, setRoute] = useState(parseHash);

  useEffect(() => {
    const onChange = () => setRoute(parseHash());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  const go = useCallback((...parts) => navigate(...parts), []);

  const { segments, params } = route;
  const [first, second] = segments;
  const view = first === "movie" ? "movie" : ROUTES.has(first) ? first : "discover";
  const movieId = first === "movie" && second ? Number(second) : null;

  return {
    view,
    movieId: Number.isFinite(movieId) ? movieId : null,
    token: params.get("token") || "",
    go,
  };
}
