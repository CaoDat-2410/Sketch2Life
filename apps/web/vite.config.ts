import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..')

// https://vite.dev/config/
export default defineConfig({
  envDir: repositoryRoot,
  plugins: [
    tailwindcss(),
    react(),
  ],
  test: {
    environment: 'jsdom',
    restoreMocks: true,
  },
})
