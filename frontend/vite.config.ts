import path from 'node:path';
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// Same-origin dev: the browser only talks to :5173 and /api is proxied to FastAPI.
// No CORS, first-party cookies, and env.apiBaseUrl stays ''.
const apiTarget = process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  server: {
    port: 5173,
    strictPort: true, // Google OAuth only allows the registered origin
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
    },
  },
});
