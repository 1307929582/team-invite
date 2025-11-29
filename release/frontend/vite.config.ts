import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3456,
    proxy: {
      '/api': {
        target: 'http://localhost:4567',
        changeOrigin: true
      }
    }
  }
})
