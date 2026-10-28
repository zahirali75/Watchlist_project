/**
 * Konfigurasi tes alur nyata (integration) — memanggil backend sungguhan.
 *
 * Dipisah dari `vite.config.js` karena tes ini butuh backend hidup di
 * VITE_API_URL dan MENULIS ke database (membuat akun uji). Jangan dijalankan
 * bersamaan dengan tes unit biasa.
 */
import { defineConfig } from "vite";

export default defineConfig({
  test: {
    environment: "node",
    globals: true,
    include: ["src/**/*.e2e.test.js"],
    testTimeout: 30000,
    hookTimeout: 30000,
    fileParallelism: false,
  },
});
