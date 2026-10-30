/**
 * Header horizontal satu baris di paling atas:
 * logo · Home · Movies · Watchlist · Genres · Profile · [pencarian] · akun.
 *
 * Tombol notifikasi sengaja tidak ada: backend belum punya fitur notifikasi.
 * Di layar kecil navigasi pindah ke menu hamburger dan pencarian ke tombol ikon.
 */
import React, { useEffect, useRef, useState } from "react";
import {
  Bookmark,
  ChevronDown,
  Globe,
  House,
  LayoutGrid,
  LogOut,
  Menu,
  MessageSquare,
  Search,
  Shield,
  UserRound,
  X,
} from "lucide-react";

import { useAuth } from "../../context/AuthContext.jsx";
import Logo from "./Logo.jsx";
import SearchBar from "./SearchBar.jsx";

/** Menu utama — sumber tunggal untuk header dan menu hamburger. */
export const NAV_ITEMS = [
  { view: "home", label: "Home", icon: House },
  { view: "movies", label: "Movies", icon: LayoutGrid },
  { view: "watchlist", label: "Watchlist", icon: Bookmark },
  { view: "genres", label: "Genres", icon: Globe },
  { view: "profile", label: "Profile", icon: UserRound },
];

const ACCOUNT_ITEMS = [
  { view: "profile", label: "Profile", icon: UserRound },
  { view: "watchlist", label: "My Watchlist", icon: Bookmark },
  { view: "my-reviews", label: "My Reviews", icon: MessageSquare },
];
const ADMIN_ITEMS = [
  { view: "admin", label: "Catalog Admin", icon: Shield },
  { view: "moderation", label: "Review Moderation", icon: Shield },
];

export default function TopBar({ view, query, onNavigate, onOpenAuth, onSearch }) {
  const { user, isAuthenticated, isAdmin, signOut } = useAuth();
  const [accountOpen, setAccountOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const accountRef = useRef(null);

  const displayName = user?.name || user?.email?.split("@")[0] || "Member";
  const initial = displayName.slice(0, 1).toUpperCase();
  // Detail film dianggap bagian dari Movies untuk penanda aktif.
  const activeView = view === "movie" ? "movies" : view;

  useEffect(() => {
    if (!accountOpen) return undefined;
    const close = (event) => {
      if (event.type === "keydown" ? event.key === "Escape" : !accountRef.current?.contains(event.target)) {
        setAccountOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [accountOpen]);

  function go(item) {
    setAccountOpen(false);
    setDrawerOpen(false);
    onNavigate(item);
  }

  function search(value) {
    setSearchOpen(false);
    setDrawerOpen(false);
    onSearch(value);
  }

  function navButton(item, extraClass = "") {
    const Icon = item.icon;
    const active = activeView === item.view;
    return (
      <button
        type="button"
        key={item.view + item.label}
        className={`${extraClass}${active ? " active" : ""}`.trim()}
        aria-current={active ? "page" : undefined}
        onClick={() => go(item)}
      >
        <Icon size={18} aria-hidden="true" />
        <span>{item.label}</span>
      </button>
    );
  }

  return (
    <header className="topbar">
      <div className="topbar-row">
        <Logo onClick={() => go({ view: "home" })} />

        <nav className="main-nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => navButton(item))}
        </nav>

        <SearchBar className="topbar-search" query={query} onSearch={search} />

        <div className="topbar-tools">
          <button
            type="button"
            className="icon-btn mobile-only"
            aria-label="Search"
            aria-expanded={searchOpen}
            onClick={() => setSearchOpen((open) => !open)}
          >
            <Search size={20} aria-hidden="true" />
          </button>

          {isAuthenticated ? (
            <div className="account" ref={accountRef}>
              <button
                type="button"
                className="account-trigger"
                aria-haspopup="menu"
                aria-expanded={accountOpen}
                aria-label={`Account menu for ${displayName}`}
                onClick={() => setAccountOpen((open) => !open)}
              >
                <span className="avatar" aria-hidden="true">
                  {initial}
                </span>
                <ChevronDown size={15} aria-hidden="true" />
              </button>
              {accountOpen ? (
                <div className="account-menu" role="menu">
                  <div className="account-menu-head">
                    <strong>{displayName}</strong>
                    <small>{user?.email}</small>
                    {isAdmin ? <em className="role-badge">admin</em> : null}
                  </div>
                  {ACCOUNT_ITEMS.map((item) => {
                    const Icon = item.icon;
                    return (
                      <button type="button" role="menuitem" key={item.view} onClick={() => go(item)}>
                        <Icon size={16} aria-hidden="true" /> {item.label}
                      </button>
                    );
                  })}
                  {isAdmin
                    ? ADMIN_ITEMS.map((item) => {
                        const Icon = item.icon;
                        return (
                          <button type="button" role="menuitem" key={item.view} onClick={() => go(item)}>
                            <Icon size={16} aria-hidden="true" /> {item.label}
                          </button>
                        );
                      })
                    : null}
                  <button
                    type="button"
                    role="menuitem"
                    className="danger"
                    onClick={() => {
                      setAccountOpen(false);
                      signOut();
                    }}
                  >
                    <LogOut size={16} aria-hidden="true" /> Logout
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="auth-links">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => onOpenAuth("login")}>
                Login
              </button>
              <button type="button" className="btn btn-gold btn-sm" onClick={() => onOpenAuth("register")}>
                Register
              </button>
            </div>
          )}

          <button
            type="button"
            className="icon-btn mobile-only"
            aria-label={drawerOpen ? "Close menu" : "Open menu"}
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen((open) => !open)}
          >
            {drawerOpen ? <X size={22} aria-hidden="true" /> : <Menu size={22} aria-hidden="true" />}
          </button>
        </div>
      </div>

      {searchOpen ? (
        <div className="mobile-search">
          <SearchBar query={query} onSearch={search} autoFocus />
        </div>
      ) : null}

      {drawerOpen ? (
        <nav className="mobile-drawer" aria-label="Mobile navigation">
          {NAV_ITEMS.map((item) => navButton(item))}
        </nav>
      ) : null}
    </header>
  );
}
