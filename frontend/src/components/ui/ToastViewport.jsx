/** Tampilan notifikasi aksi (toast) dari ToastProvider. */

import React from "react";
import { CheckCircle2, Info, X, XCircle } from "lucide-react";

import { useToast } from "../../context/ToastContext.jsx";

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
};

export default function ToastViewport() {
  const { toasts, dismiss } = useToast();
  if (!toasts.length) return null;

  return (
    <div className="toast-viewport" role="region" aria-label="Notifikasi" aria-live="polite">
      {toasts.map((toast) => {
        const Icon = ICONS[toast.tone] ?? Info;
        return (
          <div className={`toast toast--${toast.tone}`} key={toast.id}>
            <Icon size={16} aria-hidden="true" />
            <span>{toast.message}</span>
            <button type="button" onClick={() => dismiss(toast.id)} aria-label="Tutup notifikasi">
              <X size={14} aria-hidden="true" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
