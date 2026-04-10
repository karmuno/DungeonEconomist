import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { execSync } from 'child_process'
import { resolve } from 'path'

function getAppVersion(): string {
  // In Docker builds, version is passed as APP_VERSION env var since
  // .git/ and scripts/ aren't available in the frontend build stage.
  if (process.env.APP_VERSION) {
    return process.env.APP_VERSION
  }
  try {
    const repoRoot = resolve(__dirname, '..')
    return execSync('bash scripts/get-version.sh', { cwd: repoRoot, encoding: 'utf-8' }).trim()
  } catch {
    return 'v0.0.0-unknown'
  }
}

export default defineConfig({
  plugins: [vue()],
  define: {
    __APP_VERSION__: JSON.stringify(getAppVersion()),
  },
  server: {
    port: 5173,
    proxy: {
      // Use trailing-slash prefixes so bare SPA routes like /parties, /expeditions
      // are NOT proxied (they should be handled by the Vue router).
      '/auth/': 'http://localhost:8000',
      '/keeps/': 'http://localhost:8000',
      '/adventurers/': 'http://localhost:8000',
      '/parties/': 'http://localhost:8000',
      '/expeditions/': 'http://localhost:8000',
      '/time/': 'http://localhost:8000',
      '/dashboard/': 'http://localhost:8000',
      '/dungeon/': 'http://localhost:8000',
      '/buildings/': 'http://localhost:8000',
      '/admin/': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
    },
  },
})
