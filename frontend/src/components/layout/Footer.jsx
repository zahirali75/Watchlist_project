/**
 * Footer. Hanya memuat tautan yang benar-benar berfungsi — newsletter, tautan
 * sosial, Help, dan halaman legal tidak ditampilkan karena belum ada tujuannya.
 */
import React from "react";

import Logo, { ReelIcon } from "./Logo.jsx";
import { NAV_ITEMS } from "./TopBar.jsx";

export default function Footer({ onNavigate }) {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <Logo onClick={() => onNavigate({ view: "home" })} />
          <p>Your Movie Journey, Organized.</p>
        </div>
        <nav className="footer-links" aria-label="Quick links">
          <h2>Quick Links</h2>
          <ul>
            {NAV_ITEMS.map((item) => (
              <li key={item.view}>
                <button type="button" onClick={() => onNavigate(item)}>
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
        <ReelIcon size={120} className="footer-reel" />
      </div>
      <div className="footer-bottom">© {new Date().getFullYear()} MovieWatchlist. All rights reserved.</div>
    </footer>
  );
}
