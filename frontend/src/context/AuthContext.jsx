/**
 * Konteks autentikasi: satu tempat untuk token, profil, dan perpanjangan sesi.
 *
 * Kenapa dipisah dari komponen: sebelumnya seluruh state auth hidup di App.jsx
 * bersama state katalog, sehingga setiap perubahan filter ikut me-render ulang
 * logika login. Di sini hanya identitas & sesi.
 *
 * KEAMANAN (sengaja tidak diubah, hanya dilengkapi):
 * - Token tetap disimpan di `sessionStorage` seperti versi sebelumnya (bukan
 *   localStorage). sessionStorage hilang saat tab ditutup = paparan lebih pendek.
 * - Access token backend berumur 60 menit (ACCESS_TOKEN_EXPIRE_MINUTES). Versi
 *   lama hanya menyimpan access token dan membuang refreshToken, sehingga sesi
 *   mati begitu token habis. Sekarang refresh token ikut disimpan (refresh token
 *   di-hash di database dan dirotasi setiap dipakai — lihat migrasi 0005).
 * - Tidak ada token yang pernah masuk URL, log, atau console.
 */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { ApiError, authApi } from "../api/index.js";

const STORAGE_KEY = "watchlist-auth";
const AuthContext = createContext(null);

/** Baca sesi tersimpan. Rusak/JSON tidak valid → dianggap belum login. */
function readStoredSession() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.accessToken) return null;
    return parsed;
  } catch {
    return null;
  }
}

function persistSession(session) {
  try {
    if (session) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    else sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // private mode / storage penuh: sesi tetap hidup di memori sampai tab ditutup
  }
}

function toSession(payload) {
  return {
    accessToken: payload.accessToken,
    refreshToken: payload.refreshToken ?? null,
    userId: payload.userId,
    email: payload.email,
    name: payload.name ?? null,
    role: payload.role ?? "user",
  };
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(readStoredSession);
  const [profile, setProfile] = useState(null);
  const [profileError, setProfileError] = useState("");
  // Menandai proses "sudah pernah coba refresh" agar tidak berputar tanpa henti.
  const refreshPromise = useRef(null);

  const applySession = useCallback((next) => {
    setSession(next);
    persistSession(next);
    return next;
  }, []);

  const signOut = useCallback(() => {
    setProfile(null);
    setProfileError("");
    applySession(null);
  }, [applySession]);

  /**
   * Perpanjang sesi memakai refresh token. Dijamin hanya satu permintaan jalan
   * pada satu waktu: beberapa komponen yang gagal bersamaan akan menunggu
   * promise yang sama, bukan menembak /auth/refresh berkali-kali.
   */
  const refreshSession = useCallback(async () => {
    if (!session?.refreshToken) return null;
    if (refreshPromise.current) return refreshPromise.current;

    const running = (async () => {
      try {
        const payload = await authApi.refreshSession(session.refreshToken);
        return applySession(toSession(payload));
      } catch {
        // Refresh token mati/kedaluwarsa → sesi dianggap berakhir, bukan error keras.
        signOut();
        return null;
      } finally {
        refreshPromise.current = null;
      }
    })();

    refreshPromise.current = running;
    return running;
  }, [applySession, session?.refreshToken, signOut]);

  /**
   * Pembungkus pemanggilan API: kalau backend menjawab 401 sekali, sesi
   * diperpanjang lalu permintaan diulang. 401 kedua = sesi benar-benar berakhir.
   */
  const withAuth = useCallback(
    async (call, { retry = true } = {}) => {
      if (!session?.accessToken) throw new ApiError("Kamu belum masuk.", { status: 401 });
      try {
        return await call(session.accessToken);
      } catch (error) {
        if (retry && error instanceof ApiError && error.isUnauthorized) {
          const renewed = await refreshSession();
          if (renewed?.accessToken) return call(renewed.accessToken);
        }
        throw error;
      }
    },
    [refreshSession, session?.accessToken],
  );

  const signIn = useCallback(
    async ({ email, password }) => {
      const payload = await authApi.login({ email, password });
      applySession(toSession(payload));
      return payload;
    },
    [applySession],
  );

  const signUp = useCallback(
    async ({ email, password, name }) => {
      const payload = await authApi.register({ email, password, name });
      return applySession(toSession(payload));
    },
    [applySession],
  );

  const signOutEverywhere = useCallback(async () => {
    const token = session?.accessToken;
    const refreshToken = session?.refreshToken;
    // Cabut sesi di server dulu (kalau gagal, tetap keluar secara lokal: pengguna
    // tidak boleh terjebak dalam sesi yang tidak bisa ditutup).
    if (token && refreshToken) {
      try {
        await authApi.logout(refreshToken, token);
      } catch {
        /* diabaikan dengan sengaja */
      }
    }
    signOut();
  }, [session?.accessToken, session?.refreshToken, signOut]);

  /** Ambil profil sendiri. Dipakai halaman Profil (endpoint /users/me). */
  const loadProfile = useCallback(async () => {
    if (!session) return null;
    try {
      const data = await withAuth((token) => authApi.getMyProfile(token));
      setProfile(data);
      setProfileError("");
      return data;
    } catch (error) {
      setProfileError(error.message);
      return null;
    }
  }, [session, withAuth]);

  const saveProfile = useCallback(
    async (name) => {
      const data = await withAuth((token) => authApi.updateMyProfile(name, token));
      setProfile(data);
      // Nama di header ikut berubah tanpa perlu login ulang.
      setSession((current) => {
        if (!current) return current;
        const next = { ...current, name: data?.name ?? current.name };
        persistSession(next);
        return next;
      });
      return data;
    },
    [withAuth],
  );

  useEffect(() => {
    if (session && !profile) loadProfile();
    // Hanya bergantung pada identitas: memuat profil ulang di setiap perubahan
    // objek sesi (mis. setelah refresh token) tidak perlu.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.userId]);

  const value = useMemo(
    () => ({
      session,
      user: session,
      isAuthenticated: Boolean(session?.accessToken),
      isAdmin: session?.role === "admin",
      profile,
      profileError,
      signIn,
      signUp,
      signOut: signOutEverywhere,
      refreshSession,
      withAuth,
      loadProfile,
      saveProfile,
    }),
    [
      session,
      profile,
      profileError,
      signIn,
      signUp,
      signOutEverywhere,
      refreshSession,
      withAuth,
      loadProfile,
      saveProfile,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth harus dipakai di dalam <AuthProvider>.");
  return context;
}
