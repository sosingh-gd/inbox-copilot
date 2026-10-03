/// <reference types="vitest/config" />
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
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    env: { VITE_GOOGLE_CLIENT_ID: 'test-client-id', VITE_API_BASE_URL: 'http://localhost' },
  },
});
