import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Serve docs/ as static assets — data.json & staging_checks.json live there
  publicDir: 'docs',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
