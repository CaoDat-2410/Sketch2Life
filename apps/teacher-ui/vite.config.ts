import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

const workspaceRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..')

function findRootEnvDirectory(start: string): string {
  let directory = start
  while (directory !== dirname(directory)) {
    const hasProjectMarkers = existsSync(resolve(directory, '.git'))
      && existsSync(resolve(directory, 'compose.yaml'))
    if (hasProjectMarkers && existsSync(resolve(directory, '.env'))) return directory
    directory = dirname(directory)
  }
  return start
}

const rootEnvDirectory = findRootEnvDirectory(workspaceRoot)

// https://vite.dev/config/
export default defineConfig({
  envDir: rootEnvDirectory,
  plugins: [
    tailwindcss(),
    react(),
  ],
  test: {
    environment: 'jsdom',
    restoreMocks: true,
  },
})
