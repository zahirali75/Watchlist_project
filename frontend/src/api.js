const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status, code, meta) {
    super(message);
    this.status = status;
    this.code = code;
    this.meta = meta;
  }
}

export async function api(path, { method = "GET", token, body, query } = {}) {
  const url = new URL(`${API_BASE}${path}`);
  for (const [key, value] of Object.entries(query || {})) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  }
  let response;
  try {
    response = await fetch(url, {
      method,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("The API could not be reached. Check the backend and network.", 0, "NETWORK_ERROR");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const meta = data.data?.errorMeta;
    const category = meta?.category;
    const databaseMessage = response.status === 502 ? {
      connection: "FastAPI is running, but it cannot reach PostgreSQL. Verify the backend DATABASE_URL host/port, DNS, and Supabase network access.",
      schema: "The database schema is behind the API. Review the migration plan and apply Alembic migrations to the intended database.",
      permission: "The database account lacks required table privileges. Check grants and the RLS role requirements before changing permissions.",
    }[category] : undefined;
    throw new ApiError(databaseMessage || data.message || "Request failed", response.status, data.data?.errorCode, meta);
  }
  return data;
}
