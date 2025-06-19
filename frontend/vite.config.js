import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // This is critical for AWS Amplify/SDK to work correctly in Vite.
      // It ensures the browser-compatible version of the AWS JS SDK is used.
      './runtimeConfig': './runtimeConfig.browser',
    },
  },
});
