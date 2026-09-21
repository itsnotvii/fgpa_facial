import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  css: { postcss: {} }, // no PostCSS config needed; skips searching parent folders for one
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000', //fastApi runs automatically on 8000 default
      '/video_feed': 'http://127.0.0.1:8000',
      '/snapshot.jpg': 'http://127.0.0.1:8000',
    },
  },
})