import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // API_PORT: canli ilovaga tegmasdan alohida dev API bilan sinash uchun
    proxy: { '/api': `http://localhost:${process.env.API_PORT || 8000}` },
  },
})
