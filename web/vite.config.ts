import { defineConfig } from 'vite'
import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

import { resolve } from 'node:path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [viteReact(), tailwindcss()],
  envDir: '../',
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // React core
          if (id.includes('react') || id.includes('react-dom')) {
            return 'react-vendor'
          }

          // TanStack libraries
          if (id.includes('@tanstack')) {
            return 'tanstack-vendor'
          }

          // Radix UI components
          if (id.includes('@radix-ui')) {
            return 'radix-vendor'
          }

          // Effect ecosystem
          if (id.includes('effect') || id.includes('@effect')) {
            return 'effect-vendor'
          }

          // Syntax highlighters
          if (
            id.includes('react-syntax-highlighter') ||
            id.includes('prismjs') ||
            id.includes('shiki')
          ) {
            return 'syntax-vendor'
          }

          // Large visualization libraries
          if (
            id.includes('cytoscape') ||
            id.includes('mermaid') ||
            id.includes('@xyflow')
          ) {
            return 'visualization-vendor'
          }

          // AI/LLM related
          if (id.includes('/ai') || id.includes('ai/')) {
            return 'ai-vendor'
          }

          // Supabase
          if (id.includes('@supabase')) {
            return 'supabase-vendor'
          }

          // Other node_modules
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
      },
    },
  },
})
