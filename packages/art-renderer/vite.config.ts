import {resolve} from 'node:path';

import {defineConfig} from 'vite';

export default defineConfig({
  build: {
    outDir: 'dist-demo',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'demo.html'),
    },
  },
});
