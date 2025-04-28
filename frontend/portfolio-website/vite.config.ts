import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    hmr: {
      overlay: false
    }
  },
  clearScreen: false,
  build: {
    rollupOptions: {
      onwarn(warning, warn) {
        if (warning.code === 'THIS_IS_UNDEFINED') return;
        warn(warning);
      }
    }
  }
});
