/// <reference types="vitest/config" />
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

// Paths served by Frappe. In development Vite proxies them; in production the
// reverse proxy does the same, so the browser always talks to ONE origin and
// Frappe's session cookie + CSRF token work without CORS.
const BACKEND_PATHS = ['/api', '/assets', '/files', '/private', '/socket.io', '/app', '/desk']

// The app is served by Frappe at /hostelsuite/ (see pg_managment_system/frontend.py).
const BASE = '/hostelsuite/'
// nginx strips trailing slashes (/hostelsuite/ → /hostelsuite), so the PWA scope
// must not end in '/'. The backend sends `Service-Worker-Allowed` for this.
const SCOPE = '/hostelsuite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.FRAPPE_URL || 'http://127.0.0.1:8000'
  const site = env.FRAPPE_SITE || 'hostel_management.local'

  return {
    base: BASE,
    plugins: [
      vue(),
      tailwindcss(),
      VitePWA({
        registerType: 'prompt', // show "update available" toast instead of silently reloading
        injectRegister: false,
        scope: SCOPE,
        includeAssets: ['favicon.ico', 'icons/apple-touch-icon-180x180.png', 'offline.html'],
        manifest: {
          id: BASE,
          name: 'HostelSuite – Hostel & PG Management',
          short_name: 'HostelSuite',
          description: 'Manage PG properties, tenants, rent, electricity and payments.',
          start_url: `${SCOPE}?source=pwa`,
          scope: SCOPE,
          display: 'standalone',
          display_override: ['standalone', 'minimal-ui'],
          orientation: 'any',
          lang: 'en-IN',
          dir: 'ltr',
          prefer_related_applications: false,
          // reuse an open app window instead of stacking new ones (links, shortcuts, notifications)
          launch_handler: { client_mode: ['navigate-existing', 'auto'] },
          theme_color: '#4338ca',
          background_color: '#f8fafc',
          categories: ['business', 'finance', 'productivity'],
          icons: [
            { src: 'icons/pwa-64x64.png', sizes: '64x64', type: 'image/png' },
            { src: 'icons/pwa-192x192.png', sizes: '192x192', type: 'image/png' },
            { src: 'icons/pwa-512x512.png', sizes: '512x512', type: 'image/png' },
            { src: 'icons/maskable-icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
          ],
          shortcuts: [
            { name: 'Collect payment', url: `${BASE}payments/collect`, icons: [{ src: 'icons/pwa-192x192.png', sizes: '192x192' }] },
            { name: 'Tenants', url: `${BASE}tenants`, icons: [{ src: 'icons/pwa-192x192.png', sizes: '192x192' }] },
            { name: 'Rooms', url: `${BASE}rooms`, icons: [{ src: 'icons/pwa-192x192.png', sizes: '192x192' }] },
          ],
          // shown in the richer install dialog (Chrome / Edge)
          screenshots: [
            { src: 'screenshots/narrow.png', sizes: '780x1688', type: 'image/png', form_factor: 'narrow', label: 'Sign in on your phone' },
            { src: 'screenshots/wide.png', sizes: '1280x800', type: 'image/png', form_factor: 'wide', label: 'HostelSuite on desktop' },
          ],
        },
        workbox: {
          // Only the static app shell is precached. Business data and private
          // files are NEVER cached (NetworkOnly) – see runtimeCaching below.
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
          globIgnores: ['screenshots/**'], // install-dialog only, not needed offline
          navigateFallback: `${BASE}index.html`,
          navigateFallbackDenylist: [/^\/api\//, /^\/app/, /^\/desk/, /^\/files\//, /^\/private\//, /^\/assets\//, /^\/socket\.io/],
          cleanupOutdatedCaches: true,
          importScripts: ['push-sw.js'], // relative to the SW, i.e. /hostelsuite/push-sw.js
          runtimeCaching: [
            { urlPattern: ({ url }) => url.pathname.startsWith('/api/'), handler: 'NetworkOnly' },
            { urlPattern: ({ url }) => url.pathname.startsWith('/private/'), handler: 'NetworkOnly' },
            {
              // public Frappe static assets (logos etc.) – safe to cache
              urlPattern: ({ url }) => url.pathname.startsWith('/assets/') && /\.(png|svg|jpg|jpeg|webp|woff2)$/.test(url.pathname),
              handler: 'CacheFirst',
              options: { cacheName: 'frappe-static', expiration: { maxEntries: 60, maxAgeSeconds: 7 * 24 * 3600 } },
            },
          ],
        },
        devOptions: { enabled: false },
      }),
    ],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      port: 5173,
      proxy: Object.fromEntries(
        BACKEND_PATHS.map((p) => [
          p,
          { target, changeOrigin: false, ws: p === '/socket.io', headers: { Host: site } },
        ]),
      ),
    },
    preview: { port: 4173 },
    build: {
      target: 'es2022',
      sourcemap: false,
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('echarts') || id.includes('zrender')) return 'charts'
              if (id.includes('reka-ui') || id.includes('@floating-ui')) return 'ui'
              if (id.includes('lucide')) return 'icons'
              return 'vendor'
            }
          },
        },
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      include: ['src/**/*.spec.ts'],
    },
  }
})
