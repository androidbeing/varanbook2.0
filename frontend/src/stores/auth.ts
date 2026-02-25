import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import type { User, LoginPayload } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // ── State ──────────────────────────────────────────────────────────────────
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ── Getters ────────────────────────────────────────────────────────────────
  const isAuthenticated = computed(() => !!accessToken.value)
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')
  const isAdmin = computed(() =>
    user.value?.role === 'super_admin' || user.value?.role === 'admin',
  )

  // ── Actions ────────────────────────────────────────────────────────────────
  function _persist(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function _clear() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function login(payload: LoginPayload) {
    loading.value = true
    error.value = null
    try {
      const tokens = await authApi.login(payload)
      _persist(tokens.access_token, tokens.refresh_token)
      await fetchMe()
    } catch (e: unknown) {
      const msg =
        e instanceof Error ? e.message : 'Login failed. Check your credentials.'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!accessToken.value) return
    try {
      user.value = await authApi.me()
    } catch {
      _clear()
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // ignore – still clear local state
    } finally {
      _clear()
    }
  }

  // Restore user on app boot if token exists
  if (accessToken.value && !user.value) {
    fetchMe()
  }

  return {
    accessToken,
    refreshToken,
    user,
    loading,
    error,
    isAuthenticated,
    isSuperAdmin,
    isAdmin,
    login,
    logout,
    fetchMe,
  }
})
