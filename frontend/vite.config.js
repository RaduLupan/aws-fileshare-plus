// vite.config.js
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on mode (development, production)
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [react()],
    resolve: {
      alias: [
        {
          find: './runtimeConfig',
          replacement: './runtimeConfig.browser',
        },
      ],
    },
    define: {
      global: 'window', // Polyfill 'global' to 'window' for browser compatibility
    },
    // Properly handle environment variables
    // In Vite, env variables are exposed through import.meta.env instead of process.env
    envPrefix: 'VITE_', // Only expose variables that start with VITE_
    // For esbuild optimization
    optimizeDeps: {
      esbuildOptions: {
        define: {
          global: 'globalThis',
        },
      },
    },
    server: {
      port: 3000,
      strictPort: true,
      // Add CORS headers for development
      cors: true,
    },
    build: {
      // Generate source maps for debugging
      sourcemap: true,
      // Output location - dist folder is the default
      outDir: 'dist',
    }
  };
});