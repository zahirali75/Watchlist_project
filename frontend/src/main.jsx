import React from "react";
import { createRoot } from "react-dom/client";

import App from "./App.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import { ToastProvider } from "./context/ToastContext.jsx";
import "./styles.css";

const container = document.getElementById("root");

createRoot(container).render(
  <React.StrictMode>
    <ToastProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ToastProvider>
  </React.StrictMode>,
);
