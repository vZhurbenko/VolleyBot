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
  const redirect = route.query.redirect
  return redirect && (redirect.match(/\/t\/([a-f0-9-]+)/i) || redirect.match(/\/guest\/training\/([a-f0-9-]+)/i))
})

const trainingUuid = computed(() => {
  const redirect = route.query.redirect
  // Проверяем /t/{uuid}
  let match = redirect?.match(/\/t\/([a-f0-9-]+)/i)
  if (match) return match[1]
  // Проверяем /guest/training/{uuid}
  match = redirect?.match(/\/guest\/training\/([a-f0-9-]+)/i)
  return match ? match[1] : null
})

// Обработка кнопки
const handleRedirectOrAdmin = () => {
  const redirect = route.query.redirect
  const trainingRedirectMatch = redirect ? redirect.match(/\/t\/([a-f0-9-]+)/i) : null
  const trainingUuid = trainingRedirectMatch ? trainingRedirectMatch[1] : null
  const isGuest = authStore.user?.is_guest ?? false
  
  if (redirect && trainingRedirectMatch) {
    const uuid = trainingUuid
    if (isGuest) {
      console.log('[LoginView] Гость редиректится на страницу гостя:', `/guest/training/${uuid}`)
      window.location.href = `/guest/training/${uuid}`
    } else {
      console.log('[LoginView] Пользователь редиректится на календарь:', `/dashboard/calendar?training=${uuid}`)
      window.location.href = `/dashboard/calendar?training=${uuid}`
    }
  } else {
    console.log('[LoginView] Переход на /admin')
    window.location.href = '/admin'
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
  
  // Проверяем /t/{uuid}
  let trainingRedirectMatch = redirect ? redirect.match(/\/t\/([a-f0-9-]+)/i) : null
  // Проверяем /guest/training/{uuid}
  if (!trainingRedirectMatch) {
    trainingRedirectMatch = redirect ? redirect.match(/\/guest\/training\/([a-f0-9-]+)/i) : null
  }
  const trainingUuid = trainingRedirectMatch ? trainingRedirectMatch[1] : null

  const authData = { ...user }
  if (trainingUuid) {
    authData.training_uuid = trainingUuid
    console.log('[LoginView] Авторизация с training_uuid:', trainingUuid)
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
      const isAdmin = result.user?.is_admin ?? false

      if (redirect && trainingRedirectMatch) {
        const uuid = trainingUuid
        if (isGuest) {
          console.log('[LoginView] Гость редиректится на страницу гостя:', `/guest/training/${uuid}`)
          window.location.href = `/guest/training/${uuid}`
        } else {
          // Пользователь или админ → календарь с модалкой записи
          console.log('[LoginView] Пользователь/админ редиректится на календарь:', `/dashboard/calendar?training=${uuid}`)
          window.location.href = `/dashboard/calendar?training=${uuid}`
        }
      } else {
        // Нет redirect — админ идёт в админку, пользователь в календарь
        if (isAdmin) {
          console.log('[LoginView] Админ перенаправляется в админку')
          window.location.href = '/admin'
        } else {
          console.log('[LoginView] Пользователь перенаправляется в календарь')
          window.location.href = '/dashboard/calendar'
        }
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

onMounted(async () => {
  console.log('[LoginView] onMounted вызван')
  console.log('[LoginView] route.query.redirect:', route.query.redirect)
  
  // Проверяем, авторизован ли уже пользователь
  try {
    const response = await fetch('/api/auth/me', {
      credentials: 'include',
    })
    if (response.ok) {
      const user = await response.json()
      authStore.setUser(user)
      console.log('[LoginView] Пользователь уже авторизован:', user)

      const isGuest = user?.is_guest ?? false
      const isAdmin = user?.is_admin ?? false
      const redirect = route.query.redirect

      if (redirect) {
        // Проверяем /t/{uuid}
        let trainingRedirectMatch = redirect.match(/\/t\/([a-f0-9-]+)/i)
        // Проверяем /guest/training/{uuid}
        if (!trainingRedirectMatch) {
          trainingRedirectMatch = redirect.match(/\/guest\/training\/([a-f0-9-]+)/i)
        }

        if (trainingRedirectMatch) {
          const uuid = trainingRedirectMatch[1]
          if (isGuest) {
            console.log('[LoginView] Гость перенаправляется на страницу гостя:', `/guest/training/${uuid}`)
            window.location.href = `/guest/training/${uuid}`
          } else {
            // Пользователь или админ → календарь с модалкой
            console.log('[LoginView] Пользователь/админ перенаправляется на календарь:', `/dashboard/calendar?training=${uuid}`)
            window.location.href = `/dashboard/calendar?training=${uuid}`
          }
          return
        }
      } else {
        // Нет redirect — админ идёт в админку, пользователь в календарь
        if (isAdmin) {
          console.log('[LoginView] Админ перенаправляется в админку')
          window.location.href = '/admin'
          return
        } else if (!isGuest) {
          console.log('[LoginView] Пользователь перенаправляется в календарь')
          window.location.href = '/dashboard/calendar'
          return
        }
      }
    }
  } catch (error) {
    console.error('[LoginView] Ошибка проверки авторизации:', error)
  }
  
  loadTelegramConfig()
})

onBeforeUnmount(() => {
  const container = document.getElementById('telegram-login')
  if (container) {
    container.innerHTML = ''
  }
})
</script>
