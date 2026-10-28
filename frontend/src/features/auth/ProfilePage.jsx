/**
 * Halaman profil sendiri. Memakai endpoint yang sebelumnya tidak dipakai
 * antarmuka sama sekali:
 *   - GET  /users/me        → data profil
 *   - PUT  /users/me        → ubah nama tampilan
 *   - GET  /users/me/stats  → ringkasan watchlist
 *   - POST /auth/change-password → ganti password (wajib password lama)
 */
import React, { useEffect, useState } from "react";
import { KeyRound, UserRound } from "lucide-react";

import { authApi, watchlistApi } from "../../api/index.js";
import { ErrorState, LoadingState } from "../../components/ui/States.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useToast } from "../../context/ToastContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { formatDate } from "../../lib/format.js";

export default function ProfilePage() {
  const { session, user, withAuth, saveProfile } = useAuth();
  const toast = useToast();

  const { data: profile, loading, error, reload } = useAsyncData(
    () => withAuth((token) => authApi.getMyProfile(token)),
    [],
  );

  // stats memakai bentuk camelCase: { total, watched, watching, wantToWatch }
  const stats = useAsyncData(() => withAuth((token) => authApi.getMyStats(token)), []);

  const [name, setName] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [nameError, setNameError] = useState("");

  const [passwordForm, setPasswordForm] = useState({ currentPassword: "", newPassword: "", confirm: "" });
  const [passwordError, setPasswordError] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    if (profile?.name) setName(profile.name);
  }, [profile?.name]);

  async function onSubmitName(event) {
    event.preventDefault();
    if (!name.trim()) {
      setNameError("Nama tidak boleh kosong.");
      return;
    }
    setSavingName(true);
    setNameError("");
    try {
      await saveProfile(name.trim());
      toast.success("Profil diperbarui.");
      reload();
    } catch (caught) {
      setNameError(caught.message);
    } finally {
      setSavingName(false);
    }
  }

  async function onSubmitPassword(event) {
    event.preventDefault();
    if (passwordForm.newPassword.length < 8) {
      setPasswordError("Password baru minimal 8 karakter.");
      return;
    }
    if (passwordForm.newPassword !== passwordForm.confirm) {
      setPasswordError("Konfirmasi password tidak sama.");
      return;
    }
    setSavingPassword(true);
    setPasswordError("");
    try {
      await withAuth((token) => authApi.changePassword(passwordForm, token));
      setPasswordForm({ currentPassword: "", newPassword: "", confirm: "" });
      toast.success("Password berhasil diganti.");
    } catch (caught) {
      setPasswordError(caught.status === 401 ? "Password lama salah." : caught.message);
    } finally {
      setSavingPassword(false);
    }
  }

  if (loading) return <LoadingState label="Memuat profil…" />;
  if (error) return <ErrorState error={error} onRetry={reload} title="Gagal memuat profil" />;

  const counts = stats.data ?? {};
  const rows = [
    { label: "Total", value: counts.total ?? 0 },
    { label: "Ingin ditonton", value: counts.wantToWatch ?? 0 },
    { label: "Sedang ditonton", value: counts.watching ?? 0 },
    { label: "Sudah ditonton", value: counts.watched ?? 0 },
  ];

  return (
    <div className="profile-layout">
      <section className="profile-card">
        <div className="form-title">
          <UserRound size={17} aria-hidden="true" /> PROFIL
        </div>
        <dl className="profile-facts">
          <div>
            <dt>Email</dt>
            <dd>{profile?.email || user?.email || "—"}</dd>
          </div>
          <div>
            <dt>Peran</dt>
            <dd>{profile?.role || session?.role || "user"}</dd>
          </div>
          <div>
            <dt>Terdaftar</dt>
            <dd>{formatDate(profile?.created_at)}</dd>
          </div>
        </dl>

        <form onSubmit={onSubmitName}>
          <label>
            Nama tampilan
            <input maxLength={255} value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          {nameError ? (
            <p className="form-error" role="alert">
              {nameError}
            </p>
          ) : null}
          <button className="primary-button" type="submit" disabled={savingName}>
            {savingName ? "Menyimpan…" : "Simpan nama"}
          </button>
        </form>
      </section>

      <aside className="profile-side">
        <section className="profile-card">
          <div className="form-title">RINGKASAN WATCHLIST</div>
          {stats.loading ? (
            <p className="list-muted">Memuat…</p>
          ) : stats.error ? (
            <p className="form-error">{stats.error.message}</p>
          ) : (
            <ul className="stats-list">
              {rows.map((row) => (
                <li key={row.label}>
                  <span>{row.label}</span>
                  <strong>{row.value}</strong>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="profile-card">
          <div className="form-title">
            <KeyRound size={17} aria-hidden="true" /> GANTI PASSWORD
          </div>
          <form onSubmit={onSubmitPassword}>
            <label>
              Password saat ini
              <input
                required
                type="password"
                autoComplete="current-password"
                value={passwordForm.currentPassword}
                onChange={(event) => setPasswordForm({ ...passwordForm, currentPassword: event.target.value })}
              />
            </label>
            <label>
              Password baru
              <input
                required
                minLength={8}
                type="password"
                autoComplete="new-password"
                value={passwordForm.newPassword}
                onChange={(event) => setPasswordForm({ ...passwordForm, newPassword: event.target.value })}
              />
              <small className="field-hint">Minimal 8 karakter.</small>
            </label>
            <label>
              Ulangi password baru
              <input
                required
                minLength={8}
                type="password"
                autoComplete="new-password"
                value={passwordForm.confirm}
                onChange={(event) => setPasswordForm({ ...passwordForm, confirm: event.target.value })}
              />
            </label>
            {passwordError ? (
              <p className="form-error" role="alert">
                {passwordError}
              </p>
            ) : null}
            <button className="primary-button" type="submit" disabled={savingPassword}>
              {savingPassword ? "Menyimpan…" : "Ganti password"}
            </button>
          </form>
        </section>
      </aside>

      <p className="panel-note">
        Status watchlist yang tersedia: {watchlistApi.WATCH_STATUSES.join(", ")}.
      </p>
    </div>
  );
}
