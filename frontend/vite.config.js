import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/monitoring': 'http://localhost:8000',
      '/data': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
      '/forecast': 'http://localhost:8000',
      '/models': 'http://localhost:8000',
      '/analysis': 'http://localhost:8000',
      '/health': 'http://localhost:8000'
    }
  }
})
