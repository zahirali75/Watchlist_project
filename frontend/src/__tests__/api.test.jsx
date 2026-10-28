import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, moviesApi, requestList, requestData, reviewsApi } from "../api/index.js";
import { AuthProvider, useAuth } from "../context/AuthContext.jsx";

/** Bangun Response palsu dengan bentuk body JSON seperti backend. */
function jsonResponse(body, { status = 200 } = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
  };
}

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
});

describe("klien API", () => {
  it("mengirim method, header Authorization, dan body JSON yang benar", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ success: true, data: { id: 1 } }));

    await requestData("/movies", { method: "POST", token: "abc", body: { title: "X" } });

    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toBe("http://127.0.0.1:8000/movies");
    expect(init.method).toBe("POST");
    expect(init.headers.Authorization).toBe("Bearer abc");
    expect(init.headers["Content-Type"]).toBe("application/json");
    expect(init.body).toBe(JSON.stringify({ title: "X" }));
  });

  it("membuang query kosong dan menyertakan query yang terisi", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ success: true, data: [] }));

    await requestList("/movies", { query: { search: "", genre: "Drama", media_type: undefined, limit: 20 } });

    const url = new URL(String(fetchMock.mock.calls[0][0]));
    expect(url.searchParams.get("genre")).toBe("Drama");
    expect(url.searchParams.get("limit")).toBe("20");
    expect(url.searchParams.has("search")).toBe(false);
    expect(url.searchParams.has("media_type")).toBe(false);
  });

  it("membuka envelope daftar berhalaman (count/total sejajar dengan data)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ success: true, count: 2, total: 140, page: 1, limit: 2, data: [{ id: 1 }, { id: 2 }] }),
    );

    const result = await requestList("/movies");

    expect(result.items).toHaveLength(2);
    expect(result.total).toBe(140);
    expect(result.count).toBe(2);
  });

  it("melempar ApiError berisi status, kode, dan pesan dari backend", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        { success: false, message: "Judul wajib diisi", data: { errorCode: "VALIDATION_ERROR" } },
        { status: 422 },
      ),
    );

    const error = await moviesApi.createMovie({ title: "" }, "token").catch((caught) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(422);
    expect(error.code).toBe("VALIDATION_ERROR");
    expect(error.message).toBe("Judul wajib diisi");
  });

  it("memetakan error 422 FastAPI ke field yang salah", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        {
          success: false,
          message: "Data tidak valid",
          data: {
            errorCode: "VALIDATION_ERROR",
            errors: [{ location: ["body", "title"], message: "field required" }],
          },
        },
        { status: 422 },
      ),
    );

    const error = await moviesApi.createMovie({}, "token").catch((caught) => caught);

    expect(error.fieldMessage("title")).toBe("field required");
    expect(error.fieldMessage("genre")).toBe("");
  });

  it("memberi penjelasan khusus untuk kegagalan database (502)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        { success: false, message: "Bad Gateway", data: { errorCode: "DB_UNAVAILABLE", errorMeta: { category: "connection" } } },
        { status: 502 },
      ),
    );

    const error = await moviesApi.listMovies().catch((caught) => caught);

    expect(error.message).toMatch(/PostgreSQL/);
    expect(error.status).toBe(502);
  });

  it("menandai kegagalan jaringan sebagai status 0", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));

    const error = await moviesApi.listMovies().catch((caught) => caught);

    expect(error.status).toBe(0);
    expect(error.isNetworkError).toBe(true);
  });

  it("mengirim payload yang cocok dengan skema backend (bukan field karangan)", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ success: true, data: {} }));

    await moviesApi.createMovie(
      {
        title: "Contoh",
        release_year: 2024,
        genre: "Drama",
        director: "Sutradara",
        overview: "",
        poster_url: "",
        rating: 7.5,
        media_type: "series",
      },
      "token",
    );

    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(Object.keys(body).sort()).toEqual(
      ["director", "genre", "media_type", "overview", "poster_url", "rating", "release_year", "title"].sort(),
    );
    expect(body.media_type).toBe("series");
    // Field yang dulu dikirim tetapi tidak ada di skema backend:
    expect(body).not.toHaveProperty("tmdb_id");
    expect(body).not.toHaveProperty("genres");
    expect(body).not.toHaveProperty("release_date");
    expect(body).not.toHaveProperty("poster_path");
  });

  it("PUT /reviews hanya mengirim field yang berubah (parsial)", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ success: true, data: {} }));

    await reviewsApi.updateReview(9, { content: "teks baru" }, "token");

    expect(fetchMock.mock.calls[0][1].method).toBe("PUT");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ content: "teks baru" });
  });

  it("memakai endpoint moderasi yang benar untuk admin", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ success: true, data: {} }));

    await reviewsApi.moderateReview(5, true, "token");

    expect(String(fetchMock.mock.calls[0][0])).toBe("http://127.0.0.1:8000/reviews/5/moderation");
    expect(fetchMock.mock.calls[0][1].method).toBe("PATCH");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ is_hidden: true });
  });
});

function AuthProbe() {
  const { isAuthenticated, user, signIn, signOut } = useAuth();
  return (
    <div>
      <span data-testid="state">{isAuthenticated ? `masuk:${user.email}` : "keluar"}</span>
      <button type="button" onClick={() => signIn({ email: "uji@example.com", password: "rahasia123" })}>
        masuk
      </button>
      <button type="button" onClick={signOut}>
        keluar
      </button>
    </div>
  );
}

describe("konteks autentikasi", () => {
  it("menyimpan sesi ke sessionStorage dan menandai pengguna masuk", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        success: true,
        userId: "u-1",
        email: "uji@example.com",
        name: "Uji",
        role: "user",
        accessToken: "access-1",
        refreshToken: "refresh-1",
      }),
    );

    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "masuk" }));

    await waitFor(() => expect(screen.getByTestId("state")).toHaveTextContent("masuk:uji@example.com"));

    const stored = JSON.parse(sessionStorage.getItem("watchlist-auth"));
    expect(stored.accessToken).toBe("access-1");
    // Perbaikan: refresh token ikut disimpan supaya sesi bisa diperpanjang
    // setelah access token (60 menit) habis.
    expect(stored.refreshToken).toBe("refresh-1");
    expect(localStorage.getItem("watchlist-auth")).toBeNull();
  });

  it("membersihkan sesi saat keluar", async () => {
    sessionStorage.setItem(
      "watchlist-auth",
      JSON.stringify({ accessToken: "a", refreshToken: "r", userId: "u", email: "x@y.z", role: "user" }),
    );
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ success: true, data: { id: "u", email: "x@y.z" } }));

    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "keluar" }));

    await waitFor(() => expect(screen.getByTestId("state")).toHaveTextContent("keluar"));
    expect(sessionStorage.getItem("watchlist-auth")).toBeNull();
  });
});
