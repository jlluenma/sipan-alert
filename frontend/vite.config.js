import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Reutiliza los recursos de marca existentes; no duplica logos ni imágenes.
  publicDir: '../app/assets',
  server: { port: 5173 },
})
