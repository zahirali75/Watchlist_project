/**
 * Kerangka halaman: header + konten + navigasi bawah (layar kecil) + footer.
 *
 * Dulu seluruh struktur ini menempel di App.jsx bersama logika data, sehingga
 * sulit membedakan "layout" dan "state aplikasi". Sekarang App hanya mengurus
 * data dan navigasi; tampilan bersama ada di sini.
 *
 * Bilah navigasi bawah memakai daftar menu dan handler yang SAMA dengan header
 * (TopBar.bottomNavItems + onNavigate), jadi rute yang ditempuh identik —
 * hanya tempatnya yang berbeda di layar kecil.
 */
import React from "react";

import { useAuth } from "../../context/AuthContext.jsx";
import ToastViewport from "../ui/ToastViewport.jsx";
import TopBar, { bottomNavItems } from "./TopBar.jsx";

export default function AppShell({ view, mediaType, onNavigate, onOpenAuth, children }) {
  const { isAuthenticated, isAdmin } = useAuth();
  const bottomItems = bottomNavItems({ isAuthenticated, isAdmin });

  return (
    <div className="app-shell">
      <TopBar view={view} mediaType={mediaType} onNavigate={onNavigate} onOpenAuth={onOpenAuth} />
      <main>{children}</main>
      <footer>
        <span>
          CINELIST <i>·</i> KATALOG FILM &amp; SERIES
        </span>
        <span>DATA LANGSUNG DARI API BACKEND</span>
      </footer>

      <nav className="bottom-nav" aria-label="Navigasi bawah">
        {bottomItems.map((item) => {
          const Icon = item.icon;
          const active = view === item.view && (item.mediaType === undefined || item.mediaType === mediaType);
          return (
            <button
              type="button"
              key={item.label}
              className={active ? "active" : ""}
              aria-current={active ? "page" : undefined}
              onClick={() => onNavigate(item)}
            >
              <Icon size={19} aria-hidden="true" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <ToastViewport />
    </div>
  );
}
