/**
 * Halaman lupa password & atur ulang password.
 *
 * Endpoint ini sudah ada di backend sejak migrasi 0006 tetapi belum pernah
 * dipakai antarmuka. Karena email pengiriman bersifat opsional (`SMTP_HOST`
 * kosong = tautan hanya ditulis ke log server), halaman ini sengaja TIDAK
 * mengklaim "email terkirim", melainkan menampilkan pesan netral yang sama
 * seperti backend untuk mencegah penebakan email terdaftar.
 */
import React, { useState } from "react";
import { MailCheck, KeyRound } from "lucide-react";

import { authApi } from "../../api/index.js";
import { useToast } from "../../context/ToastContext.jsx";

export function ForgotPasswordPage({ onBackToLogin }) {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(event) {
    event.preventDefault();
    if (!email.trim()) {
      setError("Email wajib diisi.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      await authApi.forgotPassword(email.trim());
      setSent(true);
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-modal auth-modal--inline">
        <div className="eyebrow">PEMULIHAN AKUN</div>
        <h2>
          Lupa password<span className="title-period">.</span>
        </h2>

        {sent ? (
          <div className="auth-page-result" role="status">
            <MailCheck size={22} aria-hidden="true" />
            <p>
              Kalau email <strong>{email}</strong> terdaftar, tautan atur ulang sudah dibuat. Di lingkungan
              pengembangan tanpa SMTP, tautan itu tertulis di log server, bukan dikirim lewat email.
            </p>
            <button type="button" className="text-action" onClick={onBackToLogin}>
              Kembali ke halaman masuk
            </button>
          </div>
        ) : (
          <form onSubmit={onSubmit} noValidate>
            <label>
              Email akun
              <input
                required
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
              />
            </label>
            {error ? (
              <p className="form-error" role="alert">
                {error}
              </p>
            ) : null}
            <button className="primary-button" type="submit" disabled={busy}>
              {busy ? "Memproses…" : "Kirim tautan atur ulang"}
            </button>
            <p className="switch-auth">
              <button type="button" onClick={onBackToLogin}>
                Kembali
              </button>
            </p>
          </form>
        )}
      </div>
    </section>
  );
}

export function ResetPasswordPage({ token, onDone }) {
  const toast = useToast();
  const [form, setForm] = useState({ newPassword: "", confirm: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    if (!token) {
      setError("Tautan tidak memuat token. Minta tautan baru dari halaman lupa password.");
      return;
    }
    if (form.newPassword.length < 8) {
      setError("Password baru minimal 8 karakter.");
      return;
    }
    if (form.newPassword !== form.confirm) {
      setError("Konfirmasi password tidak sama.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      await authApi.resetPassword({ token, newPassword: form.newPassword });
      toast.success("Password berhasil diatur ulang. Silakan masuk.");
      onDone();
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-modal auth-modal--inline">
        <div className="eyebrow">PEMULIHAN AKUN</div>
        <h2>
          Password baru<span className="title-period">.</span>
        </h2>
        <form onSubmit={onSubmit} noValidate>
          <label>
            Password baru
            <input
              required
              type="password"
              minLength={8}
              value={form.newPassword}
              onChange={(event) => setForm({ ...form, newPassword: event.target.value })}
              autoComplete="new-password"
            />
            <small className="field-hint">Minimal 8 karakter.</small>
          </label>
          <label>
            Ulangi password baru
            <input
              required
              type="password"
              minLength={8}
              value={form.confirm}
              onChange={(event) => setForm({ ...form, confirm: event.target.value })}
              autoComplete="new-password"
            />
          </label>
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
          <button className="primary-button" type="submit" disabled={busy}>
            <KeyRound size={16} aria-hidden="true" />
            {busy ? "Menyimpan…" : "Simpan password baru"}
          </button>
        </form>
      </div>
    </section>
  );
}
