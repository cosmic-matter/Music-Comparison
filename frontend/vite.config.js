import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    allowedHosts: [
      'beat-buddy-3.preview.emergentagent.com',
      '.emergentagent.com',
      'localhost',
      '127.0.0.1'
    ]
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
  esbuild: {
    loader: 'jsx',
    include: /src\/.*\.[jt]sx?$/,
    exclude: [],
  },
  optimizeDeps: {
    esbuildOptions: {
      plugins: [
        {
          name: 'load-js-files-as-jsx',
          setup(build) {
            build.onLoad({ filter: /src\/.*\.js$/ }, async (args) => ({
              loader: 'jsx',
              contents: await require('fs').promises.readFile(args.path, 'utf8'),
            }))
          },
        },
      ],
    },
  },
  define: {
    // Replace process.env with import.meta.env for Vite
    'process.env': 'import.meta.env',
  },
})