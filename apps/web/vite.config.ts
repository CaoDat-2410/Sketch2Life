import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'
import { loadEnv } from 'vite'

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..')

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repositoryRoot, '')
  const apiTarget =
    env.VITE_API_PROXY_TARGET?.trim() ||
    `http://127.0.0.1:${env.SKETCH2LIFE_API_PORT || '8000'}`

  return {
    envDir: repositoryRoot,
    server: {
      allowedHosts: (env.SKETCH2LIFE_WEB_ALLOWED_HOSTS || '').split(',').map((host) => host.trim()).filter(Boolean),
      proxy: {
        '/api': { target: apiTarget, changeOrigin: true },
        '/health': { target: apiTarget, changeOrigin: true },
        // Teacher/School Manager calls under /v1 (lesson occurrences, uploads, notifications) use a relative base URL
        // in dev; without this proxy the Vite server answers them with an empty 404.
        '/v1': { target: apiTarget, changeOrigin: true },
      },
    },
    plugins: [
      tailwindcss(),
      react(),
    ],
    test: {
      environment: 'jsdom',
      restoreMocks: true,
    },
  }
})
