import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api/chat': {
        target: process.env.VITE_AI_AGENT_URL || 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/documents': {
        target: process.env.VITE_AI_AGENT_URL || 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
