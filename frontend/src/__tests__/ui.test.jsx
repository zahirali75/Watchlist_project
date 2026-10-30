/**
 * Tes UI hasil redesign Black & Gold: membuktikan tata letak baru TIDAK memutus mata rantai
 * antara tampilan dan data.
 *
 * Yang diuji di sini bukan warna atau CSS, melainkan hal yang bisa rusak diam-
 * diam saat JSX disusun ulang:
 *   1. pemanggilan API masih memakai ID yang benar (perhatikan argumennya),
 *   2. callback (onOpen/onAdd/onNavigate/onSearch) masih menerima objek yang sama,
 *   3. UI ikut berubah setelah mutasi berhasil,
 *   4. label aksesibilitas (aria-label/aria-pressed/aria-current) masih ada,
 *   5. jalur poster: gambar dipakai bila ada URL, teks fallback bila tidak ada.
 *
 * API di-mock di sini karena yang diuji adalah perilaku tampilan; kontrak HTTP
 * yang sebenarnya diuji di api.test.jsx (mock fetch) dan flow.e2e.test.js
 * (backend sungguhan).
 */
import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../context/AuthContext.jsx";
import { ToastProvider } from "../context/ToastContext.jsx";
import AppShell from "../components/layout/AppShell.jsx";
import DiscoverPage from "../features/discover/DiscoverPage.jsx";
import HomePage from "../features/home/HomePage.jsx";
import WatchlistPage from "../features/watchlist/WatchlistPage.jsx";

const CATALOG = [
  { id: 1, title: "Echoes of Tomorrow", release_year: 2024, genre: "Sci-Fi, Drama", rating: 8.6, media_type: "movie", director: "Rani", overview: "Sinopsis satu.", poster_url: "https://example.test/echoes.jpg" },
  { id: 2, title: "Northern Light", release_year: 2021, genre: "Drama", rating: 7.2, media_type: "movie", director: "Budi", overview: "Sinopsis dua.", poster_url: "" },
];

const WATCHLIST = [
  {
    id: 9,
    movie_id: 54,
    status: "want_to_watch",
    movies: { id: 54, title: "Midnight Signal", release_year: 2022, genre: "Thriller", rating: 7.9, media_type: "movie", poster_url: "" },
  },
];

vi.mock("../api/index.js", () => {
  const WATCH_STATUS_LABELS = { want_to_watch: "Ingin ditonton", watching: "Sedang ditonton", watched: "Sudah ditonton" };
  return {
    ApiError: class ApiError extends Error {
      constructor(message, { status = 0 } = {}) {
        super(message);
        this.status = status;
        this.code = "";
      }
      fieldMessage() {
        return "";
      }
    },
    request: vi.fn(),
    requestData: vi.fn(),
    requestList: vi.fn(),
    authApi: {
      getMyProfile: vi.fn(async () => ({ id: "u-1", email: "uji@example.com", name: "Uji", role: "user", created_at: "2026-01-01T00:00:00Z" })),
      getMyStats: vi.fn(async () => ({ total: 1, wantToWatch: 1, watching: 0, watched: 0 })),
      updateMyProfile: vi.fn(async (_name, token) => ({ id: "u-1", email: "uji@example.com", name: "Uji", role: "user", token })),
      changePassword: vi.fn(),
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshSession: vi.fn(),
    },
    moviesApi: {
      listMovies: vi.fn(async () => ({ items: CATALOG, total: CATALOG.length, count: CATALOG.length, page: 1, limit: 60 })),
      getMovie: vi.fn(async () => CATALOG[0]),
      createMovie: vi.fn(),
      updateMovie: vi.fn(),
      deleteMovie: vi.fn(),
    },
    watchlistApi: {
      WATCH_STATUS_LABELS,
      WATCH_STATUSES: Object.keys(WATCH_STATUS_LABELS),
      listMyWatchlist: vi.fn(async () => ({ items: WATCHLIST, total: WATCHLIST.length, count: WATCHLIST.length })),
      addToWatchlist: vi.fn(),
      updateWatchlistItem: vi.fn(async () => ({ success: true })),
      removeWatchlistItem: vi.fn(async () => ({ success: true })),
    },
    reviewsApi: { listMovieReviews: vi.fn(), listMyReviews: vi.fn(), listReviewsForModeration: vi.fn(), createReview: vi.fn(), updateReview: vi.fn(), deleteReview: vi.fn(), moderateReview: vi.fn() },
    systemApi: { listAuditLogs: vi.fn(async () => ({ items: [], total: 0 })) },
  };
});

const { authApi, moviesApi, watchlistApi } = await import("../api/index.js");

/** Prop dasar DiscoverPage (halaman Movies); tiap tes hanya menimpa yang relevan. */
const discoverProps = (overrides = {}) => ({
  mediaType: "all",
  onMediaType: vi.fn(),
  search: "",
  onSearch: vi.fn(),
  genre: "",
  onGenre: vi.fn(),
  sort: "id",
  onSort: vi.fn(),
  onOpen: vi.fn(),
  onAdd: vi.fn(),
  ...overrides,
});

const homeProps = (overrides = {}) => ({
  watchlistVersion: 0,
  onOpen: vi.fn(),
  onAdd: vi.fn(),
  onViewAll: vi.fn(),
  onGenre: vi.fn(),
  onNavigate: vi.fn(),
  onOpenAuth: vi.fn(),
  ...overrides,
});

const shellProps = (overrides = {}) => ({
  view: "home",
  query: "",
  onNavigate: vi.fn(),
  onOpenAuth: vi.fn(),
  onSearch: vi.fn(),
  ...overrides,
});

beforeEach(() => {
  sessionStorage.setItem(
    "watchlist-auth",
    JSON.stringify({ accessToken: "token-uji", refreshToken: "refresh-uji", userId: "u-1", email: "uji@example.com", role: "user" }),
  );
});

afterEach(() => {
  sessionStorage.clear();
  vi.clearAllMocks();
});

/** Provider sesuai main.jsx: ToastProvider di luar AuthProvider. */
function renderApp(ui) {
  return render(
    <ToastProvider>
      <AuthProvider>{ui}</AuthProvider>
    </ToastProvider>,
  );
}

describe("Halaman Movies", () => {
  it("mengirim filter ke API dan memakai poster bila ada, teks fallback bila tidak", async () => {
    render(<DiscoverPage {...discoverProps({ search: "echo", genre: "Drama", sort: "rating_desc" })} />);

    expect(await screen.findByAltText("Poster Echoes of Tomorrow")).toBeInTheDocument();
    expect(screen.queryByAltText("Poster Northern Light")).toBeNull();
    expect(screen.getAllByText("Northern Light").length).toBeGreaterThan(0);

    // Pencarian/genre/urutan diteruskan ke GET /movies, bukan disaring di browser.
    expect(moviesApi.listMovies).toHaveBeenCalledWith(
      expect.objectContaining({ search: "echo", genre: "Drama", sort: "rating_desc", page: 1 }),
    );
  });

  it("meneruskan objek judul yang benar saat kartu dibuka dan ditambah ke watchlist", async () => {
    const onOpen = vi.fn();
    const onAdd = vi.fn();
    render(<DiscoverPage {...discoverProps({ onOpen, onAdd })} />);

    await userEvent.click(await screen.findByLabelText("Add Northern Light to watchlist"));
    expect(onAdd.mock.calls[0][0]).toMatchObject({ id: 2, title: "Northern Light" });

    await userEvent.click(screen.getByLabelText("Open Northern Light"));
    expect(onOpen.mock.calls.at(-1)[0]).toMatchObject({ id: 2, title: "Northern Light" });
  });

  it("menandai filter jenis yang aktif dan mengirim nilai API (movie), bukan label", async () => {
    render(<DiscoverPage {...discoverProps({ mediaType: "movie" })} />);
    await screen.findByAltText("Poster Echoes of Tomorrow");

    const group = screen.getByRole("group", { name: "Media type" });
    expect(within(group).getByRole("button", { name: "Film" })).toHaveAttribute("aria-pressed", "true");
    expect(within(group).getByRole("button", { name: "Semua" })).toHaveAttribute("aria-pressed", "false");
    expect(moviesApi.listMovies).toHaveBeenCalledWith(expect.objectContaining({ mediaType: "movie" }));
  });

  it("menampilkan empty state dengan jalan keluar saat hasil kosong", async () => {
    moviesApi.listMovies.mockResolvedValueOnce({ items: [], total: 0, count: 0, page: 1, limit: 20 });
    const onSearch = vi.fn();
    render(<DiscoverPage {...discoverProps({ search: "zzz", onSearch })} />);

    expect(await screen.findByText("No movies match")).toBeInTheDocument();
    await userEvent.click(screen.getAllByRole("button", { name: /clear filters/i })[0]);
    expect(onSearch).toHaveBeenCalledWith("");
  });
});

describe("Halaman Home", () => {
  it("memuat hero + Trending (rating_desc), New Releases (year_desc), genre, dan statistik dari API", async () => {
    renderApp(<HomePage {...homeProps()} />);

    expect(await screen.findByRole("heading", { level: 1, name: "Echoes of Tomorrow" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Trending Now" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "New Releases" })).toBeInTheDocument();

    expect(moviesApi.listMovies).toHaveBeenCalledWith(expect.objectContaining({ sort: "rating_desc", limit: 5 }));
    expect(moviesApi.listMovies).toHaveBeenCalledWith(expect.objectContaining({ sort: "year_desc", limit: 5 }));
    // Hitungan genre berasal dari `total` respons, bukan angka tetap.
    expect(moviesApi.listMovies).toHaveBeenCalledWith(expect.objectContaining({ genre: "Drama", limit: 1 }));

    // Statistik dari /users/me/stats (mock: total 1).
    await waitFor(() => expect(authApi.getMyStats).toHaveBeenCalledWith("token-uji"));
    const summary = screen.getByRole("heading", { name: "Watchlist Summary" }).closest("section");
    await waitFor(() => expect(within(summary).getByText("Total Movies").nextElementSibling).toHaveTextContent("1"));
  });

  it("tidak menampilkan Watch Trailer: backend tidak punya URL trailer", async () => {
    renderApp(<HomePage {...homeProps()} />);
    await screen.findByRole("heading", { level: 1, name: "Echoes of Tomorrow" });
    expect(screen.queryByRole("button", { name: /watch trailer/i })).toBeNull();
  });

  it("Add to Watchlist di hero memanggil onAdd dengan film yang sedang tampil", async () => {
    const onAdd = vi.fn(async () => {});
    renderApp(<HomePage {...homeProps({ onAdd })} />);

    await userEvent.click(await screen.findByRole("button", { name: /add to watchlist/i }));
    expect(onAdd).toHaveBeenCalledWith(expect.objectContaining({ id: 1, title: "Echoes of Tomorrow" }));
  });

  it("panel My Watchlist memfilter status lewat API dan mengubah status lewat menu baris", async () => {
    renderApp(<HomePage {...homeProps()} />);

    expect((await screen.findAllByText("Midnight Signal")).length).toBeGreaterThan(0);
    await userEvent.click(screen.getByRole("button", { name: /^Watching/ }));
    await waitFor(() =>
      expect(watchlistApi.listMyWatchlist).toHaveBeenCalledWith(expect.objectContaining({ status: "watching", limit: 4 })),
    );

    await userEvent.click(await screen.findByRole("button", { name: "Actions" }));
    await userEvent.click(screen.getByRole("menuitem", { name: "Mark as Watched" }));
    // Argumen pertama = id BARIS watchlist (9), bukan id film (54).
    await waitFor(() => expect(watchlistApi.updateWatchlistItem).toHaveBeenCalledWith(9, { status: "watched" }, "token-uji"));
  });

  it("pengunjung anonim melihat ajakan login, bukan watchlist atau statistik palsu", async () => {
    sessionStorage.clear();
    const onOpenAuth = vi.fn();
    renderApp(<HomePage {...homeProps({ onOpenAuth })} />);

    expect(await screen.findByText("Sign in to see your watchlist")).toBeInTheDocument();
    expect(watchlistApi.listMyWatchlist).not.toHaveBeenCalled();
    expect(authApi.getMyStats).not.toHaveBeenCalled();
    await userEvent.click(screen.getAllByRole("button", { name: "Login" })[0]);
    expect(onOpenAuth).toHaveBeenCalledWith("login");
  });
});

describe("WatchlistPage setelah redesign", () => {
  it("mengirim ID baris dan status baru yang benar saat status diubah", async () => {
    renderApp(<WatchlistPage onOpen={vi.fn()} onBrowse={vi.fn()} />);

    const select = await screen.findByLabelText("Status untuk Midnight Signal");
    expect(select).toHaveValue("want_to_watch");
    await userEvent.selectOptions(select, "watched");

    await waitFor(() => expect(watchlistApi.updateWatchlistItem).toHaveBeenCalledTimes(1));
    expect(watchlistApi.updateWatchlistItem).toHaveBeenCalledWith(9, { status: "watched" }, "token-uji");
    await waitFor(() => expect(screen.getByLabelText("Status untuk Midnight Signal")).toHaveValue("watched"));
  });

  it("menghapus memakai ID baris yang benar lalu mengganti daftar dengan empty state", async () => {
    renderApp(<WatchlistPage onOpen={vi.fn()} onBrowse={vi.fn()} />);

    await userEvent.click(await screen.findByRole("button", { name: "Hapus" }));

    await waitFor(() => expect(watchlistApi.removeWatchlistItem).toHaveBeenCalledWith(9, "token-uji"));
    await waitFor(() => expect(screen.getByRole("button", { name: "Jelajahi katalog" })).toBeInTheDocument());
  });
});

describe("Header horizontal", () => {
  it("memuat Home, Movies, Watchlist, Genres, Profile dan mengirim rute yang benar", async () => {
    const onNavigate = vi.fn();
    renderApp(
      <AppShell {...shellProps({ onNavigate })}>
        <p>isi halaman</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());

    const nav = within(screen.getByRole("banner")).getByRole("navigation", { name: "Main navigation" });
    expect(within(nav).getAllByRole("button").map((button) => button.textContent)).toEqual([
      "Home",
      "Movies",
      "Watchlist",
      "Genres",
      "Profile",
    ]);

    for (const [label, view] of [["Movies", "movies"], ["Watchlist", "watchlist"], ["Genres", "genres"], ["Profile", "profile"]]) {
      await userEvent.click(within(nav).getByRole("button", { name: label }));
      expect(onNavigate).toHaveBeenLastCalledWith(expect.objectContaining({ view }));
    }
  });

  it("menandai halaman aktif lewat aria-current (detail film = Movies)", async () => {
    const { unmount } = renderApp(
      <AppShell {...shellProps({ view: "genres" })}>
        <p>isi</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());
    const nav = () => within(screen.getByRole("banner")).getByRole("navigation", { name: "Main navigation" });
    expect(within(nav()).getByRole("button", { name: "Genres" })).toHaveAttribute("aria-current", "page");
    expect(within(nav()).getByRole("button", { name: "Home" })).not.toHaveAttribute("aria-current");
    unmount();

    renderApp(
      <AppShell {...shellProps({ view: "movie" })}>
        <p>isi</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());
    expect(within(nav()).getByRole("button", { name: "Movies" })).toHaveAttribute("aria-current", "page");
  });

  it("mengirim kata kunci saat Enter dan mengosongkannya dengan tombol clear", async () => {
    const onSearch = vi.fn();
    renderApp(
      <AppShell {...shellProps({ onSearch })}>
        <p>isi</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());

    const input = screen.getByLabelText("Search movies by title");
    await userEvent.type(input, "  echo {Enter}");
    expect(onSearch).toHaveBeenLastCalledWith("echo");

    await userEvent.click(screen.getByRole("button", { name: "Clear search" }));
    expect(onSearch).toHaveBeenLastCalledWith("");
  });

  it("menu akun memuat Profile, My Watchlist, Logout dan tidak menawarkan menu admin untuk user biasa", async () => {
    const onNavigate = vi.fn();
    renderApp(
      <AppShell {...shellProps({ onNavigate })}>
        <p>isi</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());

    await userEvent.click(screen.getByRole("button", { name: /account menu/i }));
    const menu = screen.getByRole("menu");
    expect(within(menu).getByRole("menuitem", { name: /Logout/ })).toBeInTheDocument();
    expect(within(menu).queryByRole("menuitem", { name: /Catalog Admin|Review Moderation/ })).toBeNull();

    await userEvent.click(within(menu).getByRole("menuitem", { name: /My Watchlist/ }));
    expect(onNavigate).toHaveBeenCalledWith(expect.objectContaining({ view: "watchlist" }));
  });

  it("pengunjung anonim melihat Login & Register, bukan avatar", async () => {
    sessionStorage.clear();
    const onOpenAuth = vi.fn();
    renderApp(
      <AppShell {...shellProps({ onOpenAuth })}>
        <p>isi</p>
      </AppShell>,
    );
    const header = screen.getByRole("banner");
    expect(within(header).queryByRole("button", { name: /account menu/i })).toBeNull();
    await userEvent.click(within(header).getByRole("button", { name: "Register" }));
    expect(onOpenAuth).toHaveBeenCalledWith("register");
  });

  it("tidak menampilkan tombol notifikasi (belum ada fitur notifikasi di backend)", async () => {
    renderApp(
      <AppShell {...shellProps()}>
        <p>isi</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());
    expect(screen.queryByRole("button", { name: /notification/i })).toBeNull();
  });
});
