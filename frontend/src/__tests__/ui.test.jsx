/**
 * Tes UI hasil redesign: membuktikan tata letak baru TIDAK memutus mata rantai
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

const { authApi, watchlistApi } = await import("../api/index.js");

/** Prop dasar DiscoverPage; tiap tes hanya menimpa yang relevan. */
const discoverProps = (overrides = {}) => ({
  mediaType: "all",
  onMediaType: vi.fn(),
  search: "",
  onSearch: vi.fn(),
  genre: "",
  onGenre: vi.fn(),
  onOpen: vi.fn(),
  onAdd: vi.fn(),
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

describe("DiscoverPage (beranda) setelah redesign", () => {
  it("menampilkan katalog dari API, memakai gambar poster bila ada dan teks fallback bila tidak", async () => {
    render(<DiscoverPage {...discoverProps()} />);

    expect(await screen.findByRole("heading", { name: /Echoes of Tomorrow/i })).toBeInTheDocument();
    // poster_url terisi → <img> dengan alt bermakna untuk pembaca layar.
    expect(await screen.findByAltText("Poster Echoes of Tomorrow")).toBeInTheDocument();
    // poster_url kosong → fallback teks, bukan gambar rusak.
    expect(screen.queryByAltText("Poster Northern Light")).toBeNull();
    expect(screen.getAllByText("Northern Light").length).toBeGreaterThan(0);
  });

  it("meneruskan objek judul yang benar saat kartu dibuka dan saat ditambah ke watchlist", async () => {
    const onOpen = vi.fn();
    const onAdd = vi.fn();
    render(<DiscoverPage {...discoverProps({ onOpen, onAdd })} />);

    // Kartu di dalam rail (bukan hero) — dipilih lewat aria-label tombolnya.
    const addButtons = await screen.findAllByLabelText("Tambah Northern Light ke watchlist");
    await userEvent.click(addButtons[0]);
    expect(onAdd).toHaveBeenCalledTimes(1);
    expect(onAdd.mock.calls[0][0]).toMatchObject({ id: 2, title: "Northern Light" });

    const openButtons = await screen.findAllByLabelText("Buka Northern Light");
    await userEvent.click(openButtons[0]);
    expect(onOpen).toHaveBeenCalled();
    expect(onOpen.mock.calls.at(-1)[0]).toMatchObject({ id: 2, title: "Northern Light" });
  });

  it("meneruskan ketikan pencarian ke induk dan menandai filter jenis yang aktif", async () => {
    const onSearch = vi.fn();
    render(<DiscoverPage {...discoverProps({ mediaType: "movie", onSearch })} />);

    const input = screen.getByLabelText("Cari judul film atau series");
    await userEvent.type(input, "echo");
    expect(onSearch).toHaveBeenCalled();

    // Nilai yang dikirim ke backend tetap "movie" (bukan label "Film").
    const formatGroup = screen.getByRole("group", { name: "Jenis tayangan" });
    expect(within(formatGroup).getByRole("button", { name: "Film" })).toHaveAttribute("aria-pressed", "true");
    expect(within(formatGroup).getByRole("button", { name: "Semua" })).toHaveAttribute("aria-pressed", "false");
  });
});

describe("WatchlistPage setelah redesign", () => {
  it("mengirim ID baris dan status baru yang benar saat status diubah", async () => {
    renderApp(<WatchlistPage onOpen={vi.fn()} onBrowse={vi.fn()} />);

    const select = await screen.findByLabelText("Status untuk Midnight Signal");
    expect(select).toHaveValue("want_to_watch");

    await userEvent.selectOptions(select, "watched");

    await waitFor(() => expect(watchlistApi.updateWatchlistItem).toHaveBeenCalledTimes(1));
    // Argumen pertama = id BARIS WATCHLIST (9), bukan id film (54).
    expect(watchlistApi.updateWatchlistItem).toHaveBeenCalledWith(9, { status: "watched" }, "token-uji");
    // UI ikut berubah setelah mutasi berhasil (select dibaca ulang, bukan variabel lama).
    await waitFor(() => expect(screen.getByLabelText("Status untuk Midnight Signal")).toHaveValue("watched"));
  });

  it("menghapus memakai ID baris yang benar lalu mengganti daftar dengan empty state", async () => {
    renderApp(<WatchlistPage onOpen={vi.fn()} onBrowse={vi.fn()} />);

    const hapus = await screen.findByRole("button", { name: "Hapus" });
    await userEvent.click(hapus);

    await waitFor(() => expect(watchlistApi.removeWatchlistItem).toHaveBeenCalledWith(9, "token-uji"));
    // Baris benar-benar hilang: empty state muncul menggantikan daftar.
    await waitFor(() => expect(screen.getByRole("button", { name: "Jelajahi katalog" })).toBeInTheDocument());
  });
});

describe("AppShell + navigasi setelah redesign", () => {
  it("memakai rute yang sama dengan sebelumnya saat menu diklik", async () => {
    const onNavigate = vi.fn();
    renderApp(
      <AppShell view="discover" onNavigate={onNavigate} onOpenAuth={vi.fn()}>
        <p>isi halaman</p>
      </AppShell>,
    );
    // Tunggu AuthProvider selesai memuat profil agar tidak ada state update di luar act().
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());

    const header = screen.getByRole("banner");
    // Header TIDAK lagi memuat filter jenis tayangan: dulu Film/Series ada di
    // sini SEKALIGUS sebagai chip di toolbar Discover, sehingga tampak seperti
    // baris duplikat. Sekarang hanya navigasi antar-halaman.
    expect(within(header).queryByRole("button", { name: "Film" })).toBeNull();
    expect(within(header).queryByRole("button", { name: "Series" })).toBeNull();

    await userEvent.click(within(header).getByRole("button", { name: "Discover" }));
    expect(onNavigate).toHaveBeenCalledWith(expect.objectContaining({ view: "discover", mediaType: "all" }));

    await userEvent.click(within(header).getByRole("button", { name: "Watchlist" }));
    expect(onNavigate).toHaveBeenCalledWith(expect.objectContaining({ view: "watchlist" }));
  });

  it("tidak menaruh menu Profil di header (namun tetap ada di bilah bawah)", async () => {
    renderApp(
      <AppShell view="discover" onNavigate={vi.fn()} onOpenAuth={vi.fn()}>
        <p>isi halaman</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());

    // Nama akun inilah "menu Profil" di header: menuju Profil dan ditandai
    // aktif saat halaman itu sedang dibuka. (Mock profil memakai nama "Uji".)
    const accountBtn = within(screen.getByRole("banner")).getByRole("button", { name: /uji/i });
    expect(accountBtn).toBeInTheDocument();

    // Menu Profil terpisah di header tidak ada — tujuannya sudah di nama akun.
    expect(within(screen.getByRole("banner")).queryByRole("button", { name: "Profil" })).toBeNull();
    // Di layar kecil nama akun disembunyikan, jadi Profil HARUS tetap ada di bawah.
    const bottomNav = screen.getByRole("navigation", { name: "Navigasi bawah" });
    expect(within(bottomNav).getByRole("button", { name: "Profil" })).toBeInTheDocument();
  });

  it("menandai halaman aktif di header untuk tiap rute", async () => {
    const { unmount } = renderApp(
      <AppShell view="profile" onNavigate={vi.fn()} onOpenAuth={vi.fn()}>
        <p>isi halaman</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());

    // Halaman Profil: nama akun di kanan header jadi penanda halaman aktif.
    const header = screen.getByRole("banner");
    expect(within(header).getByRole("button", { name: /uji/i })).toHaveAttribute("aria-current", "page");
    // Tidak ada tab Discover yang salah ikut menyala.
    expect(within(header).queryByRole("button", { name: "Discover", current: "page" })).toBeNull();
    unmount();

    renderApp(
      <AppShell view="discover" onNavigate={vi.fn()} onOpenAuth={vi.fn()}>
        <p>isi halaman</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());
    expect(within(screen.getByRole("banner")).getByRole("button", { name: "Discover" })).toHaveAttribute("aria-current", "page");
  });

  it("menyediakan bilah navigasi bawah dengan menu yang sama dan maksimal 5 item", async () => {
    renderApp(
      <AppShell view="watchlist" onNavigate={vi.fn()} onOpenAuth={vi.fn()}>
        <p>isi halaman</p>
      </AppShell>,
    );
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());

    const bottomNav = screen.getByRole("navigation", { name: "Navigasi bawah" });
    const buttons = within(bottomNav).getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
    expect(buttons.length).toBeLessThanOrEqual(5);
    expect(within(bottomNav).getByRole("button", { name: "Watchlist" })).toHaveAttribute("aria-current", "page");
  });

  it("tidak menawarkan menu admin untuk pengguna biasa", async () => {
    renderApp(
      <AppShell view="discover" onNavigate={vi.fn()} onOpenAuth={vi.fn()}>
        <p>isi halaman</p>
      </AppShell>,
    );
    // Tunggu AuthProvider selesai memuat profil agar tidak ada state update di luar act().
    await waitFor(() => expect(authApi.getMyProfile).toHaveBeenCalled());

    const header = screen.getByRole("banner");
    expect(within(header).queryByRole("button", { name: "Moderasi" })).toBeNull();
    expect(within(header).queryByRole("button", { name: "Katalog" })).toBeNull();
    expect(within(screen.getByRole("navigation", { name: "Navigasi bawah" })).queryByRole("button", { name: "Moderasi" })).toBeNull();
  });
});
