/**
 * Notifikasi aksi (toast). Tanpa dependensi tambahan supaya tidak menambah
 * perpustakaan hanya untuk 60 baris.
 *
 * Kenapa perlu: versi lama hanya punya satu kotak `error` di App.jsx, sehingga
 * keberhasilan aksi (tambah ke watchlist, hapus ulasan) tidak pernah terlihat
 * oleh pengguna — hanya perubahan senyap.
 */
import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

const ToastContext = createContext(null);
const DEFAULT_DURATION = 4000;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const counter = useRef(0);

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const push = useCallback(
    (message, { tone = "info", duration = DEFAULT_DURATION } = {}) => {
      if (!message) return null;
      counter.current += 1;
      const id = counter.current;
      setToasts((current) => [...current, { id, message, tone }]);
      if (duration > 0) {
        setTimeout(() => dismiss(id), duration);
      }
      return id;
    },
    [dismiss],
  );

  const value = useMemo(
    () => ({
      toasts,
      dismiss,
      notify: push,
      success: (message, options) => push(message, { ...options, tone: "success" }),
      error: (message, options) => push(message, { ...options, tone: "error" }),
      info: (message, options) => push(message, { ...options, tone: "info" }),
    }),
    [push, dismiss, toasts],
  );

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast harus dipakai di dalam <ToastProvider>.");
  return context;
}
