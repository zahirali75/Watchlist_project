/** Header aplikasi: merek, navigasi utama, dan aksi akun.
 *
 * Daftar menu di bawah ini juga dipakai bilah navigasi bawah di AppShell, jadi
 * ikon, label, dan `view`-nya adalah sumber tunggal untuk kedua navigasi —
 * jangan duplikasi daftarnya di tempat lain supaya rute tidak bisa menyimpang.
 */
import React from "react";
import { Bookmark, Clapperboard, Compass, LayoutGrid, LogIn, LogOut, Star, UserRound } from "lucide-react";

import { useAuth } from "../../context/AuthContext.jsx";
import { MEDIA_TYPE } from "../../lib/mediaType.js";

/**
 * Menu navigasi utama: satu tujuan per halaman, TANPA filter jenis tayangan.
 *
 * Dulu Film dan Series ada di sini SEKALIGUS sebagai chip filter di toolbar
 * Discover — dua kelompok tombol berlabel sama untuk fungsi yang sama, tetapi
 * hanya kelompok toolbar yang penandaan aktifnya ikut berubah, sehingga header
 * tampak seperti salinan baris di bawahnya. Filter jenis kini hanya ada di satu
 * tempat: chip di DiscoverPage (dan tetap terjangkau dari bilah bawah di layar
 * kecil lewat `bottomNavItems`).
 */
export const PUBLIC_ITEMS = [
  { view: "discover", mediaType: MEDIA_TYPE.all, label: "Discover", icon: Compass },
];

/** Menu yang butuh login. */
export const MEMBER_ITEMS = [
  { view: "watchlist", label: "Watchlist", icon: Bookmark },
  { view: "my-reviews", label: "Ulasan Saya", icon: Star },
  // Nama akun di kanan header sudah menuju Profil, jadi di layar lebar menu ini
  // mubazir (dua tombol, satu tujuan). Disimpan untuk bilah bawah layar kecil,
  // yang menyembunyikan nama akun sehingga tanpa ini Profil tak bisa dibuka.
  { view: "profile", label: "Profil", icon: UserRound, mobileOnly: true },
];

/** Menu khusus admin. */
export const ADMIN_ITEMS = [
  { view: "admin", label: "Katalog", icon: LayoutGrid },
  { view: "moderation", label: "Moderasi", icon: LayoutGrid },
];

/** Menu yang ditampilkan di bilah bawah: maksimal 5 item (aturan navigasi mobile). */
export function bottomNavItems({ isAuthenticated, isAdmin }) {
  if (!isAuthenticated) return PUBLIC_ITEMS;
  return [
    PUBLIC_ITEMS[0],
    // SEMUA MEMBER_ITEMS, termasuk yang `mobileOnly`: di layar kecil nama akun
    // disembunyikan, jadi bilah bawah inilah satu-satunya jalan ke Profil.
    ...MEMBER_ITEMS,
    ...(isAdmin ? ADMIN_ITEMS.slice(0, 1) : []),
  ].slice(0, 5);
}

export default function TopBar({ view, onNavigate, onOpenAuth }) {
  const { user, isAuthenticated, isAdmin, signOut } = useAuth();
  const displayName = user?.name || user?.email?.split("@")[0] || "Anggota";

  /**
   * Penanda aktif murni per HALAMAN, bukan per jenis tayangan.
   *
   * Dulu pembandingnya ikut memeriksa `mediaType`, karena Discover/Film/Series
   * adalah tiga menu terpisah di header. Setelah Film/Series dipindah ke chip
   * filter (satu-satunya sumber pilihan jenis), ikut membandingkan `mediaType`
   * membuat tab aktif menghilang begitu user memilih chip "Film" — header jadi
   * tampak tanpa halaman aktif. Sekarang: halaman yang sedang dibuka = tab aktif.
   */
  function isActive(item) {
    return view === item.view;
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
        {/* mobileOnly dilewati: tujuannya sudah ada di nama akun sebelah kanan. */}
        {isAuthenticated ? MEMBER_ITEMS.filter((item) => !item.mobileOnly).map(renderItem) : null}
        {isAdmin ? ADMIN_ITEMS.map(renderItem) : null}
      </nav>
      {/* Garis tipis penutup header: memisahkan baris ini dari garis yang sama
          persis di toolbar Discover, supaya header tidak terbaca sebagai
          salinan baris di bawahnya. */}
      <span className="header-rule" aria-hidden="true" />

      <div className="account-actions">
        {isAuthenticated ? (
          <>
            <button
              type="button"
              // Nama akun inilah "menu Profil" di header. Diberi penanda aktif
              // supaya di halaman Profil header tidak tampak tanpa halaman aktif
              // (tab Profil sendiri hanya ada di bilah bawah layar kecil).
              className={`account-name${view === "profile" ? " active" : ""}`}
              aria-current={view === "profile" ? "page" : undefined}
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
