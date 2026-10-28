/** Header aplikasi: merek, navigasi utama, dan aksi akun.
 *
 * Daftar menu di bawah ini juga dipakai bilah navigasi bawah di AppShell, jadi
 * ikon, label, dan `view`-nya adalah sumber tunggal untuk kedua navigasi —
 * jangan duplikasi daftarnya di tempat lain supaya rute tidak bisa menyimpang.
 */
import React from "react";
import { Bookmark, Clapperboard, Compass, Film, LayoutGrid, LogIn, LogOut, Star, Tv, UserRound } from "lucide-react";

import { useAuth } from "../../context/AuthContext.jsx";

/** Menu yang selalu tampil. */
export const PUBLIC_ITEMS = [
  { view: "discover", mediaType: "all", label: "Discover", icon: Compass },
  { view: "discover", mediaType: "movie", label: "Film", icon: Film },
  { view: "discover", mediaType: "series", label: "Series", icon: Tv },
];

/** Menu yang butuh login. */
export const MEMBER_ITEMS = [
  { view: "watchlist", label: "Watchlist", icon: Bookmark },
  { view: "my-reviews", label: "Ulasan Saya", icon: Star },
  { view: "profile", label: "Profil", icon: UserRound },
];

/** Menu khusus admin. */
export const ADMIN_ITEMS = [
  { view: "admin", label: "Katalog", icon: LayoutGrid },
  { view: "moderation", label: "Moderasi", icon: LayoutGrid },
];

/** Menu yang ditampilkan di bilah bawah: maksimal 5 item (aturan navigasi mobile). */
export function bottomNavItems({ isAuthenticated, isAdmin }) {
  if (!isAuthenticated) return PUBLIC_ITEMS;
  return [PUBLIC_ITEMS[0], ...MEMBER_ITEMS, ...(isAdmin ? ADMIN_ITEMS.slice(0, 1) : [])].slice(0, 5);
}

export default function TopBar({ view, mediaType, onNavigate, onOpenAuth }) {
  const { user, isAuthenticated, isAdmin, signOut } = useAuth();
  const displayName = user?.name || user?.email?.split("@")[0] || "Anggota";

  function isActive(item) {
    return view === item.view && (item.mediaType === undefined || item.mediaType === mediaType);
  }

  function renderItem(item) {
    const active = isActive(item);
    return (
      <button
        type="button"
        key={item.label}
        className={active ? "active" : ""}
        aria-current={active ? "page" : undefined}
        onClick={() => onNavigate(item)}
      >
        {item.label}
      </button>
    );
  }

  return (
    <header className="topbar">
      <button
        type="button"
        className="brand"
        onClick={() => onNavigate({ view: "discover", mediaType: "all" })}
        aria-label="CineList — beranda"
      >
        <span className="brand-mark">
          <Clapperboard size={19} aria-hidden="true" />
        </span>
        <span>
          CINE<span className="brand-light">LIST</span>
        </span>
      </button>

      <nav className="main-nav" aria-label="Navigasi utama">
        {PUBLIC_ITEMS.map(renderItem)}
        {isAuthenticated ? MEMBER_ITEMS.map(renderItem) : null}
        {isAdmin ? ADMIN_ITEMS.map(renderItem) : null}
      </nav>

      <div className="account-actions">
        {isAuthenticated ? (
          <>
            <button
              type="button"
              className="account-name"
              onClick={() => onNavigate({ view: "profile" })}
              title={displayName}
            >
              <UserRound size={15} aria-hidden="true" />
              <span>{displayName}</span>
              {isAdmin ? <span className="role-badge">admin</span> : null}
            </button>
            <button type="button" className="login-button" onClick={signOut} title="Keluar" aria-label="Keluar">
              <LogOut size={16} aria-hidden="true" />
              <span>Keluar</span>
            </button>
          </>
        ) : (
          <>
            <button type="button" className="register-button" onClick={() => onOpenAuth("register")}>
              Daftar
            </button>
            <button type="button" className="login-button" onClick={() => onOpenAuth("login")} aria-label="Masuk">
              <LogIn size={16} aria-hidden="true" />
              <span>Masuk</span>
            </button>
          </>
        )}
      </div>
    </header>
  );
}
