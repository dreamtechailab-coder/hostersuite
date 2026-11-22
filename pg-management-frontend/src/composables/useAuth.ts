import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const store = useAuthStore()
  const router = useRouter()
  const { user, isLoggedIn, isAdmin, roles } = storeToRefs(store)

  async function logout() {
    await store.logout()
    router.replace({ name: 'login' })
  }
  return { user, isLoggedIn, isAdmin, roles, login: store.login, logout }
}
