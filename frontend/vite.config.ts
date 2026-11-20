import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      // Service worker отдавал сайт из своего кэша, и клиенты видели новую версию только со следующего открытия
      // (на iPhone «На экране Домой» — днями). selfDestroying: у тех, у кого он уже стоит, при следующем заходе
      // удаляет себя и кэши (решение 2026-11-20). Манифест остаётся — сайт по-прежнему добавляется на экран «Домой».
      // Свежесть без него обеспечивают заголовки Cache-Control в Caddyfile.
      selfDestroying: true,
      registerType: 'autoUpdate',
      workbox: {
        navigateFallbackDenylist: [/^\/admin/],
      },
      manifest: {
        name: 'Стирка ON',
        short_name: 'СтиркаON',
        description: 'Сервис стирки и доставки одежды',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: '/icons/logo192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icons/logo512.png',
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
