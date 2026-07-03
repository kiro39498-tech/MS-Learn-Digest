import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Vite Configuration — MS Learn Digest
 * ======================================
 * The dev server proxy target is driven by the VITE_API_URL environment variable.
 *
 * Local dev (.env):
 *   VITE_API_URL=http://localhost:8000
 *   → proxy forwards /api requests to the local FastAPI backend.
 *
 * Local Docker dev (.env):
 *   VITE_API_URL=http://backend:8000  (Docker service name)
 *   → proxy forwards /api requests to the backend container.
 *
 * Production (Vercel):
 *   Vite's dev proxy is NOT used on Vercel. Axios calls go directly to
 *   VITE_API_URL (the Render backend URL). No proxy is needed in production
 *   because the frontend talks directly to the backend via HTTPS.
 *
 * No source code change is required when switching environments — only the
 * VITE_API_URL value in the environment variables changes.
 */
export default defineConfig(({ mode }) => {
  // Load env vars so the proxy target is resolved at config time.
  // Vite's loadEnv reads the correct .env file for the current mode.
  const env = loadEnv(mode, '../', '')

  // Proxy target: use VITE_API_URL from env, fall back to localhost for
  // developers who haven't created a .env yet.
  const apiTarget = env.VITE_API_URL || 'http://localhost:8000'

  return {
    plugins: [react()],

    // Load .env from the project root (one level above /frontend)
    envDir: '../',

    server: {
      host: true,
      port: 5173,
      proxy: {
        // During local development, Vite proxies /api/* to the FastAPI backend.
        // This avoids CORS issues when running the dev server (not a concern in
        // production where the built app is served directly from Vercel CDN).
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
