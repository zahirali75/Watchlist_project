/**
 * Klien HTTP tunggal untuk semua panggilan API.
 *
 * Bentuk respons backend (dokumentasi resmi: docs/api.md):
 *   - Envelope sukses  : { success, message?, data, count?, total?, page?, limit? }
 *     `count`/`total`/`page`/`limit` SEJAJAR dengan `data`, bukan di dalam objek `meta`.
 *   - Envelope error   : { success: false, message, data: { errorCode, errorMeta? } }
 *   - Login/register/refresh menaruh token di ROOT respons (bukan di dalam `data`),
 *     jadi objek root-nya yang dikembalikan apa adanya ke pemanggil.
 *
 * Semua fungsi di bawah mengembalikan payload yang SUDAH dibuka pembungkusnya
 * supaya komponen tidak perlu tahu bentuk envelope.
 */

const RAW_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
export const API_BASE = String(RAW_BASE).replace(/\/+$/, "");

/** Pesan ramah untuk kode error backend (app/core/error_handlers.py). */
const ERROR_CODE_MESSAGES = {
  HTTP_ERROR: "Permintaan ditolak server.",
  VALIDATION_ERROR: "Data yang dikirim belum valid.",
  INTERNAL_ERROR: "Terjadi kesalahan di server.",
};

/** Penjelasan tambahan untuk kegagalan koneksi database (status 502). */
const DATABASE_CATEGORY_MESSAGES = {
  connection:
    "FastAPI hidup, tetapi tidak bisa menjangkau PostgreSQL. Periksa DATABASE_URL, DNS, dan akses jaringan Supabase.",
  schema:
    "Skema database tertinggal dari API. Jalankan migrasi Alembic ke database yang dituju.",
  permission:
    "Akun database tidak punya hak akses yang dibutuhkan. Periksa grant dan peran RLS sebelum mengubah izin.",
};

export class ApiError extends Error {
  constructor(message, { status = 0, code, meta, fields } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.meta = meta;
    /** Daftar { location, message } dari error 422, siap dipetakan ke field form. */
    this.fields = fields ?? [];
  }

  /** 401 = belum login / token mati. Dipakai untuk memicu refresh atau logout. */
  get isUnauthorized() {
    return this.status === 401;
  }

  /** 403 = sudah login tapi bukan pemilik / bukan admin. */
  get isForbidden() {
    return this.status === 403;
  }

  /** 0 = server tidak terjangkau (backend mati / base URL salah). */
  get isNetworkError() {
    return this.status === 0;
  }

  /** Pesan untuk field tertentu, hasil 422 dari FastAPI. */
  fieldMessage(fieldName) {
    const hit = this.fields.find((item) =>
      (item.location || []).some((part) => String(part).toLowerCase() === fieldName.toLowerCase()),
    );
    return hit?.message ?? "";
  }
}

function buildUrl(path, query) {
  const url = new URL(`${API_BASE}${path}`);
  for (const [key, value] of Object.entries(query || {})) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  }
  return url;
}

function parseBody(text) {
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

function toApiError(response, payload) {
  const meta = payload?.data?.errorMeta;
  const code = payload?.data?.errorCode;
  const databaseMessage = response.status === 502 ? DATABASE_CATEGORY_MESSAGES[meta?.category] : undefined;
  const fallback = ERROR_CODE_MESSAGES[code] || `Permintaan gagal (HTTP ${response.status}).`;
  const fields = Array.isArray(payload?.data?.errors) ? payload.data.errors : [];
  return new ApiError(databaseMessage || payload?.message || fallback, {
    status: response.status,
    code,
    meta,
    fields,
  });
}

/**
 * Panggilan mentah. Mengembalikan payload JSON lengkap (envelope belum dibuka).
 * @param {string} path contoh "/movies"
 * @param {{method?: string, token?: string, body?: unknown, query?: object, signal?: AbortSignal}} options
 */
export async function request(path, { method = "GET", token, body, query, signal } = {}) {
  let response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      signal,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    // AbortError bukan kegagalan jaringan — dibiarkan naik apa adanya supaya
    // pemanggil bisa membedakan "dibatalkan" dari "server mati".
    if (error?.name === "AbortError") throw error;
    throw new ApiError("API tidak bisa dijangkau. Pastikan backend hidup dan jaringan tersedia.", {
      status: 0,
      code: "NETWORK_ERROR",
    });
  }

  const payload = parseBody(await response.text().catch(() => ""));
  if (!response.ok) throw toApiError(response, payload);
  return payload;
}

/** Panggilan yang langsung mengembalikan isi `data`. */
export async function requestData(path, options) {
  const payload = await request(path, options);
  return payload?.data;
}

/** Panggilan yang mengembalikan { items, total } dari daftar berhalaman. */
export async function requestList(path, options) {
  const payload = await request(path, options);
  return {
    items: Array.isArray(payload?.data) ? payload.data : [],
    total: Number(payload?.total ?? 0),
    count: Number(payload?.count ?? 0),
    page: Number(payload?.page ?? 1),
    limit: Number(payload?.limit ?? 0),
  };
}
