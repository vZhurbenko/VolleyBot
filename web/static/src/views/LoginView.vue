<template>
  <div
    class="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4"
  >
    <div class="bg-white rounded shadow p-6 lg:p-10 w-full max-w-md">
      <img :src="logo" alt="Team R Logo" class="w-20 h-20 mx-auto mb-4" />
      <h1 class="text-2xl font-bold text-gray-900 mb-2 text-center">Team R</h1>
      <p class="text-gray-500 mb-6 text-center">Система управления тренировками</p>

      <div v-if="isLoading" class="mt-6 text-center text-gray-500">
        Загрузка...
      </div>

      <div v-else-if="isAuthenticated" class="mt-6">
        <p class="text-green-600 font-medium mb-4 text-center">✓ Вы уже авторизованы</p>
        <button
          @click="goToAdmin"
          class="w-full h-11 px-6 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700"
        >
          Перейти в админ-панель
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
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import logo from '@/img/logo.svg'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isAuthenticated = ref(false)
const isLoading = ref(true)
const errorMessage = ref('')
const telegramConfigLoaded = ref(false)

console.log('=== LoginView: Компонент монтируется ===')
console.log('[LoginView] route.query:', route.query)
console.log('[LoginView] route.path:', route.path)
console.log('[LoginView] route.name:', route.name)
console.log('[LoginView] redirect:', route.query.redirect)

// Функция инициализации Telegram виджета
const initTelegramWidget = (botUsername) => {
  console.log('[LoginView] Инициализация Telegram виджета для:', botUsername)
  
  // Очищаем контейнер перед инициализацией
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
    console.log('[LoginView] Конфигурация уже загружена')
    return
  }
  
  try {
    console.log('[LoginView] Загрузка конфигурации Telegram...')
    const response = await fetch('/api/auth/telegram/config')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const config = await response.json()
    console.log('[LoginView] Конфигурация получена:', config.bot_username)
    initTelegramWidget(config.bot_username)
    telegramConfigLoaded.value = true
  } catch (error) {
    console.error('[LoginView] Ошибка загрузки конфигурации:', error)
    errorMessage.value = 'Ошибка загрузки конфигурации Telegram'
  }
}

// Глобальная функция для Telegram виджета
window.onTelegramAuth = async (user) => {
  console.log('[LoginView] onTelegramAuth вызвана, user:', user)
  console.log('[LoginView] redirect параметр:', route.query.redirect)

  try {
    const redirect = route.query.redirect
    const trainingRedirectMatch = redirect ? redirect.match(/\/t\/([a-f0-9-]+)/i) : null
    const trainingUuid = trainingRedirectMatch ? trainingRedirectMatch[1] : null

    const authData = { ...user }
    if (trainingUuid) {
      authData.training_uuid = trainingUuid
      console.log('[LoginView] Авторизация с training_uuid:', trainingUuid)
    }

    console.log('[LoginView] Отправка данных на сервер...')
    const response = await fetch('/api/auth/telegram', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(authData),
      credentials: 'include',
    })

    console.log('[LoginView] Ответ сервера:', response.status)
    const result = await response.json()
    console.log('[LoginView] Результат:', result)

    if (response.ok && result.success) {
      console.log('[LoginView] Авторизация успешна')
      authStore.setUser(result.user)

      const isGuest = result.user?.is_guest ?? false

      if (redirect) {
        if (trainingRedirectMatch) {
          const uuid = trainingUuid
          if (isGuest) {
            console.log('[LoginView] Гость редиректится на:', `/guest/training/${uuid}`)
            window.location.href = `/guest/training/${uuid}`
          } else {
            console.log('[LoginView] Пользователь редиректится на:', `/dashboard/calendar?training=${uuid}`)
            window.location.href = `/dashboard/calendar?training=${uuid}`
          }
        } else {
          console.log('[LoginView] Редирект на:', redirect)
          window.location.href = redirect
        }
      } else {
        console.log('[LoginView] Переход на /admin')
        window.location.href = '/admin'
      }
    } else {
      errorMessage.value = result.detail || 'Ошибка авторизации'
      console.error('[LoginView] Ошибка авторизации:', errorMessage.value)
      if (response.status === 403) {
        const loginWidget = document.getElementById('telegram-login')
        if (loginWidget) {
          loginWidget.classList.add('hidden')
        }
      }
    }
  } catch (error) {
    console.error('[LoginView] Ошибка:', error)
    errorMessage.value = 'Ошибка соединения с сервером'
  }
}

const goToAdmin = () => {
  router.push('/admin')
}

// Проверка авторизации при загрузке
onMounted(async () => {
  console.log('[LoginView] onMounted вызван')
  
  try {
    console.log('[LoginView] Проверка авторизации...')
    const response = await fetch('/api/auth/me', {
      credentials: 'include',
    })
    if (response.ok) {
      const user = await response.json()
      console.log('[LoginView] Пользователь авторизован:', user)
      isAuthenticated.value = true
      authStore.setUser(user)
    } else {
      console.log('[LoginView] Пользователь не авторизован')
      isAuthenticated.value = false
    }
  } catch (error) {
    console.error('[LoginView] Ошибка проверки авторизации:', error)
    isAuthenticated.value = false
  } finally {
    isLoading.value = false
    console.log('[LoginView] Загрузка завершена, isLoading = false')
  }

  // Всегда загружаем Telegram виджет (независимо от статуса авторизации)
  loadTelegramConfig()
})

// Очистка при размонтировании
onBeforeUnmount(() => {
  console.log('[LoginView] Компонент размонтируется')
  const container = document.getElementById('telegram-login')
  if (container) {
    container.innerHTML = ''
  }
})
</script>
