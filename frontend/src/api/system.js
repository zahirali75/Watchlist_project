/** Endpoint kesehatan & jejak audit (app/health/router.py, app/audit_logs/router.py). */
import { request, requestList } from "./client.js";

/** Status server. `withDatabase` menembak /health/db (benar-benar menyentuh DB). */
export function health({ withDatabase = false } = {}) {
  return request(withDatabase ? "/health/db" : "/health");
}

/**
 * Jejak audit (khusus admin). Dipakai halaman Admin untuk menampilkan aktivitas
 * terakhir — endpoint ini memang milik antarmuka, bukan endpoint internal.
 */
export function listAuditLogs({ action, page, limit, token, signal } = {}) {
  return requestList("/audit-logs", { token, signal, query: { action, page, limit } });
}
