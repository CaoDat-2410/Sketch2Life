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
      proxy: {
        '/api': { target: apiTarget, changeOrigin: true },
        '/health': { target: apiTarget, changeOrigin: true },
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
