import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: [
      '/monitoring',
      '/data',
      '/metrics',
      '/forecast',
      '/models',
      '/analysis',
      '/health',
    ].reduce((config, path) => {
      config[path] = {
        target: 'http://localhost:8000',
        changeOrigin: true,
        bypass(req) {
          const acceptHeader = req.headers.accept || '';
          if (acceptHeader.includes('text/html')) {
            return '/index.html';
          }
          return null;
        }
      };
      return config;
    }, {})
  }
})
