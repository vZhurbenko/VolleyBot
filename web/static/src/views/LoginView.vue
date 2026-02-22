<template>
  <div class="login-page">
    <div class="login-container">
      <div class="logo">🏐</div>
      <h1 class="title">VolleyBot</h1>
      <p class="subtitle">Система управления тренировками</p>
      
      <div v-if="isAuthenticated" class="already-logged-in">
        <p class="success-message">✓ Вы уже авторизованы</p>
        <button @click="goToAdmin" class="btn btn-primary btn-block">
          Перейти в админ-панель
        </button>
      </div>
      
      <div v-else class="login-form">
        <div class="admin-badge">
          🔐 Вход только для администраторов
        </div>
        
        <div id="telegram-login"></div>
        
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </div>
      
      <div class="footer">
        VolleyBot © {{ new Date().getFullYear() }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const user = computed(() => authStore.user)

const errorMessage = ref('')

onMounted(async () => {
  await authStore.checkAuth()
  loadTelegramConfig()
})

const loadTelegramConfig = async () => {
  try {
    const response = await fetch('/api/auth/telegram/config')
    const config = await response.json()
    initTelegramWidget(config.bot_username)
  } catch (error) {
    console.error('Ошибка загрузки конфигурации:', error)
    errorMessage.value = 'Ошибка загрузки конфигурации Telegram'
  }
}

const initTelegramWidget = (botUsername) => {
  const script = document.createElement('script')
  script.src = 'https://telegram.org/js/telegram-widget.js?22'
  script.setAttribute('data-telegram-login', botUsername)
  script.setAttribute('data-size', 'large')
  script.setAttribute('data-radius', '3')
  script.setAttribute('data-lang', 'ru')
  script.setAttribute('data-onauth', 'onTelegramAuth(user)')
  script.setAttribute('data-request-access', 'write')
  script.async = true

  const container = document.getElementById('telegram-login')
  if (container) {
    container.appendChild(script)
  }
}

const onTelegramAuth = async (user) => {
  console.log('Telegram user data:', user)

  try {
    const response = await fetch('/api/auth/telegram', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(user),
      credentials: 'include'
    })

    const result = await response.json()

    if (response.ok && result.success) {
      router.push('/admin')
    } else {
      errorMessage.value = result.detail || 'Ошибка авторизации'
      if (response.status === 403) {
        const loginWidget = document.getElementById('telegram-login')
        if (loginWidget) {
          loginWidget.classList.add('hidden')
        }
      }
    }
  } catch (error) {
    console.error('Ошибка:', error)
    errorMessage.value = 'Ошибка соединения с сервером'
  }
}

const goToAdmin = () => {
  router.push('/admin')
}

// Делаем функцию доступной глобально для Telegram виджета
window.onTelegramAuth = onTelegramAuth
</script>

<style scoped>
.login-page {
  @apply min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4;
}

.login-container {
  @apply bg-white rounded-xl shadow-lg p-8 w-full max-w-md text-center;
}

.logo {
  @apply text-6xl mb-4;
}

.title {
  @apply text-2xl font-bold text-gray-900 mb-2;
}

.subtitle {
  @apply text-gray-500 mb-6;
}

.admin-badge {
  @apply inline-block bg-gray-100 text-gray-600 px-4 py-2 rounded-lg text-sm font-medium mb-6;
}

.error-message {
  @apply mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm;
}

.success-message {
  @apply text-green-600 font-medium mb-4;
}

.already-logged-in {
  @apply mt-6;
}

.footer {
  @apply mt-8 text-gray-400 text-sm;
}

.btn {
  @apply px-4 py-2 rounded-lg font-medium transition-colors;
}

.btn-primary {
  @apply bg-gray-900 text-white hover:bg-gray-800;
}

.btn-block {
  @apply w-full;
}
</style>
