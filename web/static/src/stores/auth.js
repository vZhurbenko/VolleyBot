import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoading = ref(true)

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  async function checkAuth() {
    try {
      const response = await fetch('/api/auth/me', {
        credentials: 'include'
      })
      if (response.ok) {
        user.value = await response.json()
      } else {
        user.value = null
      }
    } catch (error) {
      console.error('Ошибка проверки авторизации:', error)
      user.value = null
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      })
      user.value = null
    } catch (error) {
      console.error('Ошибка выхода:', error)
    }
  }

  function setUser(userData) {
    user.value = userData
  }

  return {
    user,
    isLoading,
    isAuthenticated,
    isAdmin,
    checkAuth,
    logout,
    setUser
  }
})
