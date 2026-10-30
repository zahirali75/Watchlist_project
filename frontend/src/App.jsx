/**
 * Akar aplikasi: navigasi + perutean halaman + aksi lintas halaman.
 *
 * Peran file ini sengaja dijaga tipis. Sebelumnya App.jsx memuat 193 baris
 * berisi seluruh state data, seluruh pemanggilan API, seluruh tampilan tabel,
 * dua modal, dan formulir admin sekaligus — sehingga satu perubahan pada filter
 * katalog bisa diam-diam memengaruhi halaman lain. Setiap halaman kini mengurus
 * datanya sendiri (lihat features/*), dan App hanya:
 *   1. memetakan rute hash ke halaman,
 *   2. menyediakan aksi bersama (tambah ke watchlist, buka detail),
 *   3. menjaga aturan akses (halaman member & admin).
 */
import React, { useEffect, useState } from "react";

import { ApiError, watchlistApi } from "./api/index.js";
import AuthModal from "./components/auth/AuthModal.jsx";
import AppShell from "./components/layout/AppShell.jsx";
import PageHeading from "./components/layout/PageHeading.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import { useToast } from "./context/ToastContext.jsx";
import CatalogAdminPage from "./features/admin/CatalogAdminPage.jsx";
import { ForgotPasswordPage, ResetPasswordPage } from "./features/auth/PasswordPages.jsx";
import ProfilePage from "./features/auth/ProfilePage.jsx";
import DiscoverPage from "./features/discover/DiscoverPage.jsx";
import GenresPage from "./features/discover/GenresPage.jsx";
import HomePage from "./features/home/HomePage.jsx";
import MovieDetailPage from "./features/reviews/MovieDetailPage.jsx";
import ReviewsPage from "./features/reviews/ReviewsPage.jsx";
import WatchlistPage from "./features/watchlist/WatchlistPage.jsx";
import { buildHash, navigate, useRoute } from "./hooks/useRoute.js";
import { MEDIA_TYPE } from "./lib/mediaType.js";

/** Halaman yang wajib login, lengkap dengan judulnya. */
const MEMBER_PAGES = {
  watchlist: {
    index: "03",
    section: "KOLEKSI PRIBADI",
    title: "Watchlist kamu",
    description: "Judul yang kamu simpan, beserta status menontonnya.",
  },
  "my-reviews": {
    index: "04",
    section: "CATATAN PRIBADI",
    title: "Ulasan kamu",
    description: "Semua ulasan yang pernah kamu tulis, termasuk yang disembunyikan admin.",
  },
  profile: {
    index: "05",
    section: "AKUN",
    title: "Profil kamu",
    description: "Ubah nama tampilan, ganti password, dan lihat ringkasan watchlist.",
  },
  admin: {
    index: "06",
    section: "MEJA ADMIN",
    title: "Meja katalog",
    description: "Tambah, ubah, dan hapus judul di katalog bersama.",
  },
  moderation: {
    index: "07",
    section: "MEJA ADMIN",
    title: "Moderasi ulasan",
    description: "Tinjau semua ulasan pengguna dan sembunyikan yang melanggar.",
  },
};

function App() {
  const { isAuthenticated, isAdmin, withAuth } = useAuth();
  const toast = useToast();
  const { view, movieId, token: resetToken, go } = useRoute();

  const [dialog, setDialog] = useState("");
  const [search, setSearch] = useState("");
  const [genre, setGenre] = useState("");
  const [mediaType, setMediaType] = useState(MEDIA_TYPE.all);
  const [sort, setSort] = useState("id");
  // Naik setiap kali watchlist berubah dari luar panel Home (hero, kartu poster).
  const [watchlistVersion, setWatchlistVersion] = useState(0);

  // Hash kosong → tulis rute awal supaya tombol Back tidak keluar dari aplikasi.
  useEffect(() => {
    if (!window.location.hash) navigate("home");
  }, []);

  function openMovie(item) {
    const id = typeof item === "object" && item !== null ? item.id : item;
    if (id) window.location.hash = buildHash("movie", id);
  }

  /** Navigasi dari header, footer, dan menu akun. */
  function handleNavigate(item) {
    if (item.view === "movies") {
      setSearch("");
      setGenre("");
      setMediaType(MEDIA_TYPE.all);
      setSort("id");
    }
    go(item.view);
  }

  /** Pencarian dari header → GET /movies?search=… di halaman Movies. */
  function handleSearch(value) {
    setSearch(value);
    setGenre("");
    go("movies");
  }

  /** "View All" Trending/New Releases → katalog dengan urutan yang sama. */
  function goMovies({ nextSort = "id", nextGenre = "" } = {}) {
    setMediaType(MEDIA_TYPE.all);
    setSearch("");
    setGenre(nextGenre);
    setSort(nextSort);
    go("movies");
  }

  /** Tambah ke watchlist dari halaman mana pun. 409 = sudah ada, bukan kegagalan. */
  async function addToWatchlist(item) {
    if (!isAuthenticated) {
      setDialog("login");
      return;
    }
    try {
      await withAuth((token) => watchlistApi.addToWatchlist({ movieId: item.id, status: "want_to_watch" }, token));
      toast.success(`"${item.title}" added to your watchlist.`);
      setWatchlistVersion((value) => value + 1);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        toast.info("This title is already in your watchlist.");
      } else {
        toast.error(error.message);
      }
    }
  }

  function renderMovies() {
    return (
      <DiscoverPage
        mediaType={mediaType}
        onMediaType={setMediaType}
        search={search}
        onSearch={setSearch}
        genre={genre}
        onGenre={setGenre}
        sort={sort}
        onSort={setSort}
        onOpen={openMovie}
        onAdd={addToWatchlist}
      />
    );
  }

  function renderMemberPage() {
    const page = MEMBER_PAGES[view];
    const needsAdmin = view === "admin" || view === "moderation";

    if (!isAuthenticated) {
      return (
        <>
          <PageHeading section={page.section} index={page.index} title="Perlu masuk" description="Halaman ini butuh akun." />
          <div className="auth-gate">
            <p>Masuk atau daftar dulu untuk membuka halaman ini.</p>
            <button type="button" className="primary-button" onClick={() => setDialog("login")}>
              Masuk
            </button>
          </div>
        </>
      );
    }

    if (needsAdmin && !isAdmin) {
      return (
        <>
          <PageHeading
            section="MEJA ADMIN"
            index={page.index}
            title="Akses ditolak"
            description="Halaman ini hanya untuk admin."
          />
          <div className="auth-gate">
            <p>Akunmu berperan sebagai pengguna biasa, jadi halaman admin tidak tersedia.</p>
            <button type="button" className="primary-button" onClick={() => goMovies()}>
              Kembali ke katalog
            </button>
          </div>
        </>
      );
    }

    return (
      <>
        <PageHeading section={page.section} index={page.index} title={page.title} description={page.description} />
        {view === "watchlist" ? (
          <WatchlistPage onOpen={openMovie} onBrowse={() => goMovies()} />
        ) : view === "my-reviews" ? (
          <ReviewsPage onOpenMovie={openMovie} />
        ) : view === "moderation" ? (
          <ReviewsPage moderation onOpenMovie={openMovie} />
        ) : view === "profile" ? (
          <ProfilePage />
        ) : (
          <CatalogAdminPage onOpen={openMovie} />
        )}
      </>
    );
  }

  function renderPage() {
    if (view === "forgot-password") return <ForgotPasswordPage onBackToLogin={() => setDialog("login")} />;
    if (view === "reset-password") return <ResetPasswordPage token={resetToken} onDone={() => setDialog("login")} />;

    if (view === "movie" && movieId) {
      return (
        <>
          <PageHeading
            section="ARSIP FILM"
            index="02"
            title="Detail judul"
            description="Sinopsis, data katalog, dan ulasan penonton."
          />
          <MovieDetailPage
            movieId={movieId}
            onBack={() => goMovies()}
            onAdd={addToWatchlist}
            onRequireAuth={() => setDialog("login")}
          />
        </>
      );
    }

    if (MEMBER_PAGES[view]) return renderMemberPage();
    if (view === "movies") return renderMovies();
    if (view === "genres") return <GenresPage onGenre={(name) => goMovies({ nextGenre: name })} />;
    return (
      <HomePage
        watchlistVersion={watchlistVersion}
        onOpen={openMovie}
        onAdd={addToWatchlist}
        onViewAll={(nextSort) => goMovies({ nextSort })}
        onGenre={(name) => goMovies({ nextGenre: name })}
        onNavigate={handleNavigate}
        onOpenAuth={setDialog}
      />
    );
  }

  return (
    <>
      <AppShell view={view} query={search} onNavigate={handleNavigate} onOpenAuth={setDialog} onSearch={handleSearch}>
        {renderPage()}
      </AppShell>

      {dialog ? (
        <AuthModal
          mode={dialog}
          onClose={() => setDialog("")}
          onSwitch={setDialog}
          onForgot={() => {
            setDialog("");
            go("forgot-password");
          }}
        />
      ) : null}
    </>
  );
}

export default App;
