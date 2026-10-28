import js from "@eslint/js";
import globals from "globals";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";

export default [
  { ignores: ["dist/**", "node_modules/**", "coverage/**"] },

  js.configs.recommended,

  // Kode aplikasi (browser, JSX)
  {
    files: ["src/**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: { ...globals.browser },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    settings: { react: { version: "detect" } },
    plugins: { react, "react-hooks": reactHooks },
    rules: {
      ...react.configs.flat.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      // React 18 + transform otomatis: React tidak perlu diimpor untuk JSX.
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      // Variabel sengaja tidak dipakai ditandai dengan awalan _ (mis. argumen no-op).
      "no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "no-console": ["warn", { allow: ["warn", "error"] }],
    },
  },

  // Skrip Node (pengujian alur nyata)
  {
    files: ["scripts/**/*.mjs", "*.config.js"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: { ...globals.node },
    },
    rules: { "no-console": "off" },
  },

  // Berkas tes
  {
    files: ["src/**/*.test.{js,jsx}", "src/test/**/*.js"],
    languageOptions: { globals: { ...globals.browser, ...globals.node, ...globals.vitest } },
  },
];
