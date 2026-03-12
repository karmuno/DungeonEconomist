import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/adventurers': 'http://localhost:8000',
      '/parties': 'http://localhost:8000',
      '/players': 'http://localhost:8000',
      '/equipment': 'http://localhost:8000',
      '/supplies': 'http://localhost:8000',
      '/expeditions': 'http://localhost:8000',
      '/time': 'http://localhost:8000',
      '/upkeep': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
    },
  },
})
