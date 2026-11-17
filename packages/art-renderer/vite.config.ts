import {resolve} from 'node:path';

import {defineConfig} from 'vite';

export default defineConfig({
  base: '/renderer/',
  build: {
    outDir: 'dist-demo',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        demo: resolve(__dirname, 'demo.html'),
        mobile: resolve(__dirname, 'mobile.html'),
      },
    },
  },
});
