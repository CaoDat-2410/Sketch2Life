import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  // Keep asset URLs relative so the same Vite output also works from the
  // Android app's bundled file:///android_asset/ WebView origin.
  base: './',
  plugins: [react()],
  server: { host: '127.0.0.1' },
});
