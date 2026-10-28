/**
 * Hook untuk memuat data berhalaman dengan pencarian yang bisa dibatalkan.
 *
 * Mengapa dibuat: versi lama memanggil API langsung di dalam useEffect dengan
 * lima state setter terpisah dan tanpa pembatalan. Mengetik cepat di kolom
 * pencarian memicu beberapa permintaan sekaligus, dan jawaban yang datang
 * belakangan bisa menimpa jawaban terbaru (race condition yang terlihat sebagai
 * "hasil pencarian salah muncul"). Di sini setiap perubahan parameter
 * membatalkan permintaan sebelumnya (AbortController).
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "../api/index.js";

/**
 * @param {(options: {signal: AbortSignal}) => Promise<any>} loader
 * @param {unknown[]} deps nilai yang berubah → memicu pemuatan ulang
 * @param {{enabled?: boolean, initialData?: any}} options
 */
export function useAsyncData(loader, deps, { enabled = true, initialData = null } = {}) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(Boolean(enabled));
  const [error, setError] = useState(null);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const reload = useCallback(async () => {
    if (!enabled) return;
    const controller = new AbortController();
    const { signal } = controller;
    setLoading(true);
    setError(null);
    try {
      const result = await loaderRef.current({ signal });
      if (!signal.aborted) setData(result);
    } catch (caught) {
      if (caught?.name === "AbortError" || signal.aborted) return;
      setError(caught instanceof ApiError ? caught : new ApiError(String(caught?.message || caught)));
    } finally {
      if (!signal.aborted) setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) {
      setData(initialData);
      setLoading(false);
      setError(null);
      return undefined;
    }

    const controller = new AbortController();
    const { signal } = controller;
    setLoading(true);
    setError(null);

    loaderRef.current({ signal })
      .then((result) => {
        if (!signal.aborted) setData(result);
      })
      .catch((caught) => {
        if (caught?.name === "AbortError" || signal.aborted) return;
        setError(caught instanceof ApiError ? caught : new ApiError(String(caught?.message || caught)));
      })
      .finally(() => {
        if (!signal.aborted) setLoading(false);
      });

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, ...deps]);

  return { data, setData, loading, error, reload, clearError: () => setError(null) };
}

/**
 * Menunda nilai (dipakai untuk kolom pencarian) supaya tidak menembak API di
 * setiap ketukan tombol.
 */
export function useDebounced(value, delay = 350) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
