<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4">
    <div class="bg-white rounded shadow p-6 lg:p-10 w-full max-w-md">
      <img :src="logo" alt="Team R Logo" class="w-20 h-20 mx-auto mb-4" />
      
      <div v-if="loading" class="text-center py-8">
        <p class="text-gray-500">Загрузка...</p>
      </div>

      <div v-else-if="error" class="text-center">
        <div class="text-6xl mb-4">❌</div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Приглашение недействительно</h1>
        <p class="text-gray-500 mb-6">{{ error }}</p>
        <router-link
          to="/"
          class="inline-block px-6 py-2 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700"
        >
          На главную
        </router-link>
      </div>

      <div v-else class="text-center">
        <div class="text-6xl mb-4">🎉</div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Вас пригласили!</h1>
        <p class="text-gray-500 mb-6">
          Авторизуйтесь через Telegram, чтобы присоединиться к команде
        </p>

        <div v-if="!isAuthenticated" class="mb-6">
          <div id="telegram-login" class="flex justify-center"></div>
        </div>

        <div v-else-if="inviteAccepted" class="mb-6">
          <p class="text-green-600 font-medium mb-4">✓ Вы в команде!</p>
          <p class="text-gray-500">Перенаправление...</p>
        </div>

        <div class="mt-8 border-t border-gray-200 pt-8">
          <p class="text-center text-sm text-gray-500">
            VolleyBot © {{ new Date().getFullYear() }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import logo from '@/img/logo.svg'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()

const loading = ref(true)
const error = ref('')
const inviteCode = ref('')
const inviteInfo = ref(null)
const inviteAccepted = ref(false)

const isAuthenticated = computed(() => authStore.isAuthenticated)

onMounted(async () => {
  inviteCode.value = route.params.code

  // Проверяем приглашение
  await checkInvite()

  loading.value = false
  
  // Ждём рендера DOM
  await nextTick()
  
  // Загружаем конфиг Telegram только если нет ошибки и не авторизован
  if (!error.value && !isAuthenticated.value) {
    await loadTelegramConfig()
  }
})

const checkInvite = async () => {
  try {
    const response = await fetch(`/api/invite/${inviteCode.value}`)
    
    if (!response.ok) {
      const err = await response.json()
      error.value = err.detail || 'Приглашение не найдено'
      return
    }
    
    const data = await response.json()
    inviteInfo.value = data
  } catch (error) {
    console.error('Error checking invite:', error)
    error.value = 'Ошибка проверки приглашения'
  }
}

const loadTelegramConfig = async () => {
  try {
    const response = await fetch('/api/auth/telegram/config')
    const config = await response.json()
    initTelegramWidget(config.bot_username)
  } catch (error) {
    console.error('Ошибка загрузки конфигурации:', error)
  }
}

const initTelegramWidget = (botUsername) => {
  console.log('Инициализация Telegram виджета для:', botUsername)
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
  console.log('Контейнер для виджета:', container)
  if (container) {
    container.appendChild(script)
    console.log('Скрипт Telegram добавлен')
  } else {
    console.error('Контейнер #telegram-login не найден!')
  }
}

const onTelegramAuth = async (user) => {
  try {
    // Добавляем invite_code к данным пользователя
    const authData = {
      ...user,
      invite_code: inviteCode.value
    }
    
    const response = await fetch('/api/auth/telegram', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(authData),
      credentials: 'include'
    })

    const result = await response.json()

    if (response.ok && result.success) {
      authStore.setUser(result.user)
      notificationsStore.success('Вы успешно авторизовались!')
      
      // Автоматически принимаем приглашение после авторизации
      await acceptInvite()
    } else {
      error.value = result.detail || 'Ошибка авторизации'
    }
  } catch (error) {
    console.error('Ошибка авторизации:', error)
    error.value = 'Ошибка соединения с сервером'
  }
}

const acceptInvite = async () => {
  try {
    const user = authStore.user
    if (!user) {
      error.value = 'Пользователь не авторизован'
      return
    }
    
    const response = await fetch(`/api/invite/${inviteCode.value}/accept`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        id: user.telegram_id,
        first_name: user.first_name,
        last_name: user.last_name,
        username: user.username,
        photo_url: user.photo_url,
        auth_date: Math.floor(Date.now() / 1000),
        hash: '' // Хеш не нужен для этого эндпоинта
      })
    })

    const result = await response.json()

    if (response.ok && result.success) {
      inviteAccepted.value = true
      notificationsStore.success('Вы успешно присоединились к команде!')
      setTimeout(() => {
        router.push('/dashboard/calendar')
      }, 1500)
    } else {
      // Если приглашение уже использовано - это тоже успех
      if (response.status === 410 && result.detail === 'Приглашение уже использовано') {
        inviteAccepted.value = true
        notificationsStore.info('Вы уже в команде!')
        setTimeout(() => {
          router.push('/dashboard/calendar')
        }, 1500)
      } else {
        error.value = result.detail || 'Ошибка принятия приглашения'
      }
    }
  } catch (error) {
    console.error('Error accepting invite:', error)
    error.value = 'Ошибка принятия приглашения'
  }
}

// Делаем функцию доступной глобально для Telegram виджета
window.onTelegramAuth = onTelegramAuth
</script>
