import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy para o backend local (FastAPI em :8000)
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
      '/readings': { target: 'http://localhost:8000', changeOrigin: true },
      '/rules': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
