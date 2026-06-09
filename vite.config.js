import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { nodePolyfills } from 'vite-plugin-node-polyfills'

export default defineConfig({
  // GitHub Pages serves from /core-models/ — all asset paths must be relative to that
  base: '/core-models/',
  plugins: [
    react(),
    // Polyfills Node.js built-ins (stream, path, fs, etc.) required by exceljs
    nodePolyfills({ include: ['stream', 'path', 'fs', 'buffer', 'process', 'util', 'zlib'] }),
  ],
  // Serve docs/ as static assets — data.json & staging_checks.json live there
  publicDir: 'docs',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
