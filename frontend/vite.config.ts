import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  // In dev mode, expose the backend URL so API_BASE resolves correctly.
  // In Docker production, this is intentionally NOT set so relative URLs
  // (/api/*) flow through Nginx to the backend container.
  define: {
    'import.meta.env.VITE_API_BASE': JSON.stringify(
      process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000'
    ),
  },
});
