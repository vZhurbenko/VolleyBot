<template>
  <div
    class="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4"
  >
    <div class="bg-white rounded shadow p-6 lg:p-10 w-full max-w-md">
      <img :src="logo" alt="Team R Logo" class="w-20 h-20 mx-auto mb-4" />
      <h1 class="text-2xl font-bold text-gray-900 mb-2 text-center">Team R</h1>
      <p class="text-gray-500 mb-6 text-center">Система управления тренировками</p>

      <div v-if="authStore.isAuthenticated" class="mt-6">
        <p class="text-green-600 font-medium mb-4 text-center">✓ Вы уже авторизованы</p>
        <button
          @click="handleRedirectOrAdmin"
          class="w-full h-11 px-6 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700"
        >
          {{ hasTrainingRedirect ? 'Перейти к тренировке' : 'Перейти в админ-панель' }}
        </button>
      </div>

      <div v-else class="mt-6">
        <div id="telegram-login" class="flex justify-center mb-6"></div>

        <div
          v-if="errorMessage"
          class="mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm"
        >
          {{ errorMessage }}
        </div>
      </div>

      <div class="mt-8 border-t border-gray-200 pt-8">
        <p class="text-center text-sm text-gray-500">VolleyBot © {{ new Date().getFullYear() }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import logo from '@/img/logo.svg'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const errorMessage = ref('')
const telegramConfigLoaded = ref(false)

// Проверяем, есть ли redirect на тренировку
const hasTrainingRedirect = computed(() => {
  return route.query.redirect && route.query.redirect.match(/\/t\/([a-f0-9-]+)/i)
})

const trainingUuid = computed(() => {
  const match = route.query.redirect?.match(/\/t\/([a-f0-9-]+)/i)
  return match ? match[1] : null
})

// Автоматический редирект если авторизован и есть redirect на тренировку
watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth && hasTrainingRedirect.value && trainingUuid.value) {
    console.log('[LoginView] Автоматический редирект на тренировку:', trainingUuid.value)
    window.location.href = `/dashboard/calendar?training=${trainingUuid.value}`
  }
}, { immediate: true })

// Обработка кнопки
const handleRedirectOrAdmin = () => {
  if (hasTrainingRedirect.value && trainingUuid.value) {
    // Редирект на календарь с открытой модалкой
    window.location.href = `/dashboard/calendar?training=${trainingUuid.value}`
  } else {
    // Переход в админку
    router.push('/admin')
  }
}

// Функция инициализации Telegram виджета
const initTelegramWidget = (botUsername) => {
  const container = document.getElementById('telegram-login')
  if (!container) {
    console.error('[LoginView] Контейнер #telegram-login не найден')
    return
  }

  container.innerHTML = ''

  const script = document.createElement('script')
  script.src = 'https://telegram.org/js/telegram-widget.js?22'
  script.setAttribute('data-telegram-login', botUsername)
  script.setAttribute('data-size', 'large')
  script.setAttribute('data-radius', '3')
  script.setAttribute('data-lang', 'ru')
  script.setAttribute('data-onauth', 'onTelegramAuth(user)')
  script.setAttribute('data-request-access', 'write')
  script.async = true

  script.onload = () => {
    console.log('[LoginView] Telegram скрипт загружен')
  }

  script.onerror = (error) => {
    console.error('[LoginView] Ошибка загрузки Telegram скрипта:', error)
    errorMessage.value = 'Ошибка загрузки Telegram виджета'
  }

  container.appendChild(script)
}

// Загрузка конфигурации Telegram
const loadTelegramConfig = async () => {
  if (telegramConfigLoaded.value) {
    return
  }

  try {
    const response = await fetch('/api/auth/telegram/config')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const config = await response.json()
    initTelegramWidget(config.bot_username)
    telegramConfigLoaded.value = true
  } catch (error) {
    console.error('[LoginView] Ошибка загрузки конфигурации:', error)
    errorMessage.value = 'Ошибка загрузки конфигурации Telegram'
  }
}

// Глобальная функция для Telegram виджета
window.onTelegramAuth = async (user) => {
  const redirect = route.query.redirect
  const trainingRedirectMatch = redirect ? redirect.match(/\/t\/([a-f0-9-]+)/i) : null
  const trainingUuid = trainingRedirectMatch ? trainingRedirectMatch[1] : null

  const authData = { ...user }
  if (trainingUuid) {
    authData.training_uuid = trainingUuid
  }

  try {
    const response = await fetch('/api/auth/telegram', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(authData),
      credentials: 'include',
    })

    const result = await response.json()

    if (response.ok && result.success) {
      authStore.setUser(result.user)
      const isGuest = result.user?.is_guest ?? false

      if (redirect && trainingRedirectMatch) {
        const uuid = trainingUuid
        if (isGuest) {
          window.location.href = `/guest/training/${uuid}`
        } else {
          window.location.href = `/dashboard/calendar?training=${uuid}`
        }
      } else {
        window.location.href = '/admin'
      }
    } else {
      errorMessage.value = result.detail || 'Ошибка авторизации'
    }
  } catch (error) {
    console.error('[LoginView] Ошибка:', error)
    errorMessage.value = 'Ошибка соединения с сервером'
  }
}

const goToAdmin = () => {
  router.push('/admin')
}

onMounted(() => {
  loadTelegramConfig()
})

onBeforeUnmount(() => {
  const container = document.getElementById('telegram-login')
  if (container) {
    container.innerHTML = ''
  }
})
</script>
