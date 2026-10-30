/** Kerangka halaman: header horizontal di paling atas, konten, footer. */
import React from "react";

import ToastViewport from "../ui/ToastViewport.jsx";
import Footer from "./Footer.jsx";
import TopBar from "./TopBar.jsx";

export default function AppShell({ view, query, onNavigate, onOpenAuth, onSearch, children }) {
  return (
    <div className="app-shell">
      <TopBar view={view} query={query} onNavigate={onNavigate} onOpenAuth={onOpenAuth} onSearch={onSearch} />
      <main>{children}</main>
      <Footer onNavigate={onNavigate} />
      <ToastViewport />
    </div>
  );
}
