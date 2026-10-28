import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  // Vitest dijalankan lewat perintah `npm test`; file tes memakai jsdom.
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.js"],
    include: ["src/**/*.test.{js,jsx}"],
    restoreMocks: true,
    // Tes alur nyata (memanggil backend) sengaja dipisah: `npm run test:e2e`.
    exclude: ["node_modules/**", "dist/**", "src/**/*.e2e.test.{js,jsx}"],
  },
});
