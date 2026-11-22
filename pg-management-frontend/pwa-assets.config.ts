import { defineConfig, minimal2023Preset } from '@vite-pwa/assets-generator/config'

// Regenerate icons with: npx pwa-assets-generator
export default defineConfig({
  headLinkOptions: { preset: '2023' },
  preset: {
    ...minimal2023Preset,
    maskable: { ...minimal2023Preset.maskable, padding: 0.1, resizeOptions: { background: '#4338ca' } },
    apple: { ...minimal2023Preset.apple, padding: 0.1, resizeOptions: { background: '#4338ca' } },
  },
  images: ['public/icons/logo.svg'],
})
