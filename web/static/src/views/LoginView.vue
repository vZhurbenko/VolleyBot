<template>
  <div
    class="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4"
  >
    <div class="bg-white rounded shadow p-6 lg:p-10 w-full max-w-md">
      <img :src="logo" alt="Team R Logo" class="w-20 h-20 mx-auto mb-4" />
      <h1 class="text-2xl font-bold text-gray-900 mb-2 text-center">Team R</h1>
      <p class="text-gray-500 mb-6 text-center">Система управления тренировками</p>

      <div v-if="authStore.isLoading" class="mt-6 text-center text-gray-500">
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
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import logo from '@/img/logo.svg'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)

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
  console.log('Начало авторизации...')

  // Проверяем, есть ли redirect параметр и является ли он ссылкой на тренировку
  const redirect = route.query.redirect
  const trainingRedirectMatch = redirect ? redirect.match(/\/training\/([a-f0-9-]+)/i) : null
  const trainingUuid = trainingRedirectMatch ? trainingRedirectMatch[1] : null

  // Добавляем training_uuid в данные для авторизации если есть
  const authData = { ...user }
  if (trainingUuid) {
    authData.training_uuid = trainingUuid
    console.log('Авторизация с training_uuid:', trainingUuid)
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

    console.log('Ответ сервера:', response.status)
    const result = await response.json()
    console.log('Результат:', result)

    if (response.ok && result.success) {
      console.log('Авторизация успешна, обновляем store...')
      // Обновляем auth store перед редиректом
      authStore.setUser(result.user)

      // Проверяем, является ли пользователь гостем
      const isGuest = result.user?.is_guest ?? false
      const userTrainingUuid = result.user?.training_uuid

      if (redirect) {
        // Проверяем, является ли redirect ссылкой на тренировку /training/{uuid}
        if (trainingRedirectMatch) {
          const uuid = trainingUuid

          if (isGuest) {
            // Уже гость → страница гостя
            console.log('Гость редиректится на страницу тренировки:', uuid)
            window.location.href = `/guest/training/${uuid}`
          } else {
            // Пользователь → календарь с модалкой
            console.log('Пользователь редиректится на календарь:', uuid)
            window.location.href = `/dashboard/calendar?training=${uuid}`
          }
        } else {
          // Обычный редирект (не тренировка)
          console.log('Редирект на:', redirect)
          window.location.href = redirect
        }
      } else if (isGuest && userTrainingUuid) {
        // Гость без redirect → страница тренировки
        console.log('Гость редиректится на /guest/training/', userTrainingUuid)
        window.location.href = `/guest/training/${userTrainingUuid}`
      } else {
        // Пользователь без redirect → админка
        console.log('Переход на /admin через window.location...')
        window.location.href = '/admin'
      }
    } else {
      errorMessage.value = result.detail || 'Ошибка авторизации'
      console.error('Ошибка авторизации:', errorMessage.value)
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
