import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        navigateFallbackDenylist: [/^\/admin/],
      },
      manifest: {
        name: 'Стирки ON',
        short_name: 'СтиркиON',
        description: 'Сервис стирки и доставки одежды',
        theme_color: '#2563eb',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: '/icons/wm-192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icons/wm-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
    }),
  ],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api': 'http://localhost:8001',
      '/advertising': 'http://localhost:8001',
      '/admin': 'http://localhost:8001',
    },
  },
})
