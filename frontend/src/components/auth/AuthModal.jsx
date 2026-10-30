/**
 * Dialog masuk/daftar.
 *
 * Validasi: HTML5 + pemeriksaan di sisi klien (min 8 karakter untuk password,
 * sama dengan `RegisterUser` di app/auth/schemas.py) SEBELUM menembak API, lalu
 * error 422 dari backend dipetakan kembali ke field yang salah.
 */
import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

import { ApiError } from "../../api/index.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { useToast } from "../../context/ToastContext.jsx";
import Modal from "../ui/Modal.jsx";

export default function AuthModal({ mode, onClose, onSwitch, onForgot }) {
  const { signIn, signUp } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const isRegister = mode === "register";

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function validate() {
    if (!form.email.trim()) return "Email wajib diisi.";
    if (!isRegister && !form.password) return "Password wajib diisi.";
    if (isRegister && form.password.length < 8) return "Password minimal 8 karakter.";
    return "";
  }

  async function onSubmit(event) {
    event.preventDefault();
    const localError = validate();
    if (localError) {
      setError(localError);
      return;
    }
    setError("");
    setBusy(true);
    try {
      if (isRegister) {
        await signUp(form);
        toast.success("Akun dibuat. Selamat datang!");
      } else {
        await signIn({ email: form.email, password: form.password });
        toast.success("Berhasil masuk.");
      }
      onClose();
    } catch (caught) {
      const message =
        caught instanceof ApiError && caught.status === 401
          ? "Email atau password salah."
          : caught.message || "Gagal memproses permintaan.";
      setError(message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      eyebrow="MEMBER ACCESS"
      title={isRegister ? "Buat akunmu" : "Selamat datang kembali"}
      onClose={onClose}
    >
      <form onSubmit={onSubmit} noValidate>
        {isRegister ? (
          <label>
            Nama tampilan
            <input
              maxLength={255}
              value={form.name}
              onChange={(event) => update("name", event.target.value)}
              autoComplete="name"
            />
          </label>
        ) : null}

        <label>
          Email
          <input
            required
            type="email"
            value={form.email}
            onChange={(event) => update("email", event.target.value)}
            autoComplete="email"
          />
        </label>

        <label>
          Password
          <span className="password-field">
            <input
              required
              type={showPassword ? "text" : "password"}
              minLength={isRegister ? 8 : undefined}
              value={form.password}
              onChange={(event) => update("password", event.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword((value) => !value)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
            </button>
          </span>
          {isRegister ? <small className="field-hint">Minimal 8 karakter.</small> : null}
        </label>

        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}

        <button className="primary-button" type="submit" disabled={busy}>
          {busy ? "Memproses…" : isRegister ? "Buat akun" : "Masuk"}
        </button>
      </form>

      {!isRegister ? (
        <p className="switch-auth">
          <button type="button" onClick={onForgot}>
            Lupa password?
          </button>
        </p>
      ) : null}

      <p className="switch-auth">
        {isRegister ? "Sudah punya akun?" : "Belum punya akun?"}{" "}
        <button type="button" onClick={() => onSwitch(isRegister ? "login" : "register")}>
          {isRegister ? "Masuk" : "Daftar"}
        </button>
      </p>
    </Modal>
  );
}
