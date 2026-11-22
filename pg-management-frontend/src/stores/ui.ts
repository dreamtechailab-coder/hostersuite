import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

function read(key: string, fallback: string) {
  try {
    return localStorage.getItem(key) ?? fallback
  } catch {
    return fallback
  }
}
function write(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* ignore */
  }
}

export type Theme = 'light' | 'dark' | 'system'

export const useUiStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(read('pg.sidebarCollapsed', '0') === '1')
  const mobileNavOpen = ref(false)
  const searchOpen = ref(false)
  const theme = ref<Theme>(read('pg.theme', 'system') as Theme)

  const media = typeof window !== 'undefined' ? window.matchMedia('(prefers-color-scheme: dark)') : null
  function applyTheme() {
    const dark = theme.value === 'dark' || (theme.value === 'system' && !!media?.matches)
    document.documentElement.classList.toggle('dark', dark)
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#0f1424' : '#4338ca')
  }
  media?.addEventListener('change', applyTheme)
  watch(theme, (t) => {
    write('pg.theme', t)
    applyTheme()
  })
  watch(sidebarCollapsed, (v) => write('pg.sidebarCollapsed', v ? '1' : '0'))

  return { sidebarCollapsed, mobileNavOpen, searchOpen, theme, applyTheme }
})
