import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // Use trailing-slash prefixes so bare SPA routes like /parties, /expeditions
      // are NOT proxied (they should be handled by the Vue router).
      '/adventurers/': 'http://localhost:8000',
      '/parties/': 'http://localhost:8000',
      '/expeditions/': 'http://localhost:8000',
      '/players/': 'http://localhost:8000',
      '/time/': 'http://localhost:8000',
      '/game/': 'http://localhost:8000',
      '/upkeep/': 'http://localhost:8000',
      '/dashboard/': 'http://localhost:8000',
      '/ui/': 'http://localhost:8000',
    },
  },
})
