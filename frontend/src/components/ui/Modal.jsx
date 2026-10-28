/**
 * Modal yang bisa dipakai ulang: fokus terkurung, Escape menutup, klik latar
 * menutup. Versi lama menempelkan onMouseDown di setiap pemakaian dan tidak
 * menangani Escape maupun fokus, sehingga pengguna keyboard bisa "tersesat" di
 * halaman belakang.
 */
import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export default function Modal({ title, eyebrow, onClose, children, labelledBy = "modal-title" }) {
  const panelRef = useRef(null);

  useEffect(() => {
    const previous = document.activeElement;
    const panel = panelRef.current;
    panel?.querySelector(FOCUSABLE)?.focus();

    function onKeyDown(event) {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panel) return;
      const items = Array.from(panel.querySelectorAll(FOCUSABLE)).filter((node) => node.offsetParent !== null);
      if (!items.length) return;
      const firstItem = items[0];
      const lastItem = items[items.length - 1];
      if (event.shiftKey && document.activeElement === firstItem) {
        event.preventDefault();
        lastItem.focus();
      } else if (!event.shiftKey && document.activeElement === lastItem) {
        event.preventDefault();
        firstItem.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    const { overflow } = document.body.style;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = overflow;
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, [onClose]);

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section className="auth-modal" role="dialog" aria-modal="true" aria-labelledby={labelledBy} ref={panelRef}>
        <button type="button" className="modal-close icon-button" onClick={onClose} aria-label="Tutup">
          <X size={18} aria-hidden="true" />
        </button>
        {eyebrow ? <div className="eyebrow">{eyebrow}</div> : null}
        {title ? (
          <h2 id={labelledBy}>
            {title}
            <span className="title-period">.</span>
          </h2>
        ) : null}
        {children}
      </section>
    </div>
  );
}
