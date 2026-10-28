/** Endpoint autentikasi & profil sendiri (app/auth/router.py, app/users/me_router.py). */
import { request, requestData } from "./client.js";

/**
 * Login. Token dikembalikan di ROOT respons (bukan di dalam `data`) — jadi
 * pemanggil menerima objek root: { userId, email, name, role, accessToken, refreshToken }.
 */
export function login({ email, password }) {
  return request("/auth/login", { method: "POST", body: { email, password } });
}

export function register({ email, password, name }) {
  return request("/auth/register", {
    method: "POST",
    body: { email, password, name: name || undefined },
  });
}

export function refreshSession(refreshToken) {
  return request("/auth/refresh", { method: "POST", body: { refreshToken } });
}

export function logout(refreshToken, token) {
  return request("/auth/logout", { method: "POST", token, body: { refreshToken } });
}

export function changePassword({ currentPassword, newPassword }, token) {
  return request("/auth/change-password", {
    method: "POST",
    token,
    body: { currentPassword, newPassword },
  });
}

export function forgotPassword(email) {
  return request("/auth/forgot-password", { method: "POST", body: { email } });
}

export function resetPassword({ token: resetToken, newPassword }) {
  return request("/auth/reset-password", { method: "POST", body: { token: resetToken, newPassword } });
}

/** Profil sendiri. Butuh token; mengembalikan objek user dari `data`. */
export function getMyProfile(token) {
  return requestData("/users/me", { token });
}

export function updateMyProfile(name, token) {
  return requestData("/users/me", { method: "PUT", token, body: { name } });
}

/** Ringkasan watchlist: { total, watched, watching, wantToWatch } (camelCase). */
export function getMyStats(token) {
  return request("/users/me/stats", { token });
}
