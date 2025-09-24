import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// IMPORTANT: this must export an object (defineConfig returns an object)
export default defineConfig({
  plugins: [react()],
})
