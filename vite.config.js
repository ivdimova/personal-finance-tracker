import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: 'frontend',
  server: {
    proxy: {
      '/api': 'http://localhost:5555'
    }
  },
  build: {
    outDir: '../src/static',
    emptyOutDir: true,
  },
})