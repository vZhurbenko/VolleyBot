<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="max-w-3xl mx-auto px-4 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <img :src="logo" alt="Team R Logo" class="w-10 h-10" />
            <div>
              <h1 class="text-xl font-bold text-gray-900">Team R</h1>
              <p class="text-xs text-gray-500">Волейбольные тренировки</p>
            </div>
          </div>
          <button
            v-if="isAuthenticated"
            @click="logout"
            class="text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            Выйти
          </button>
        </div>
      </div>
    </div>

    <!-- Основной контент -->
    <div class="max-w-3xl mx-auto px-4 py-6">
      <!-- Загрузка -->
      <div v-if="loading" class="bg-white rounded-lg shadow p-8 text-center">
        <div
          class="animate-spin w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full mx-auto"
        ></div>
        <p class="mt-4 text-gray-600">Загрузка...</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="bg-white rounded-lg shadow p-8 text-center">
        <div
          class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <X class="w-8 h-8 text-red-600" />
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Ошибка</h2>
        <p class="text-gray-600 mb-4">{{ error }}</p>
        <button
          @click="loadTraining"
          class="px-4 py-2 bg-teal-600 text-white rounded hover:bg-teal-700 transition-colors"
        >
          Попробовать снова
        </button>
      </div>

      <!-- Тренировка -->
      <div v-else-if="training" class="bg-white rounded-lg shadow overflow-hidden">
        <!-- Заголовок тренировки -->
        <div class="bg-gradient-to-r from-teal-600 to-teal-700 px-6 py-6 text-white">
          <h2 class="text-2xl font-bold mb-2">{{ training.name || 'Тренировка' }}</h2>
          <div class="flex flex-wrap gap-4 text-sm opacity-90">
            <div class="flex items-center gap-2">
              <Calendar class="w-4 h-4" />
              <span>{{ formatDate(training.date) }}</span>
            </div>
            <div class="flex items-center gap-2">
              <Clock class="w-4 h-4" />
              <span>{{ training.time }}</span>
            </div>
            <div v-if="training.location" class="flex items-center gap-2">
              <MapPin class="w-4 h-4" />
              <span>{{ training.location }}</span>
            </div>
          </div>
        </div>

        <!-- Статус гостя -->
        <div v-if="isGuest" class="px-6 py-4 bg-yellow-50 border-b border-yellow-200">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
              <User class="w-5 h-5 text-yellow-700" />
            </div>
            <div class="flex-1">
              <p class="font-medium text-yellow-900">Вы записаны как гость</p>
              <p class="text-sm text-yellow-700">
                {{ user?.first_name }} {{ user?.last_name || '' }}
                <span v-if="user?.username" class="opacity-75">@{{ user.username }}</span>
              </p>
            </div>
            <button
              @click="unregister"
              class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
            >
              Отписаться
            </button>
          </div>
        </div>

        <!-- Список участников -->
        <div class="px-6 py-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            Записались ({{ registeredCount }}/12)
          </h3>

          <div v-if="participants && participants.length > 0" class="space-y-2">
            <div
              v-for="participant in sortedParticipants"
              :key="getParticipantKey(participant)"
              class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <!-- Аватар -->
              <img
                v-if="participant.photo_url"
                :src="participant.photo_url"
                alt=""
                class="w-10 h-10 rounded-full object-cover"
              />
              <div
                v-else
                class="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold text-sm"
              >
                {{ getInitials(participant) }}
              </div>

              <!-- Информация -->
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-medium text-gray-900">
                    {{ participant.first_name }} {{ participant.last_name || '' }}
                  </span>
                  <span v-if="participant.username" class="text-sm text-gray-400">
                    @{{ participant.username }}
                  </span>
                </div>
                <div class="flex items-center gap-2 mt-0.5">
                  <!-- Значок роли -->
                  <span
                    v-if="getParticipantRole(participant) === 'admin'"
                    class="text-yellow-600"
                    title="Администратор"
                  >
                    👑
                  </span>
                  <span
                    v-else-if="getParticipantRole(participant) === 'guest'"
                    class="text-purple-600"
                    title="Гость"
                  >
                    👤
                  </span>
                  <span v-else class="text-teal-600" title="Участник"> ✅ </span>
                  <span class="text-xs text-gray-500">
                    {{ getParticipantRoleText(participant) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-8 text-gray-500">Пока никто не записался</div>
        </div>

        <!-- Кнопка поделиться -->
        <div class="px-6 py-4 border-t border-gray-100 bg-gray-50">
          <button
            @click="shareLink"
            class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors font-medium"
          >
            <Link class="w-5 h-5" />
            Поделиться ссылкой
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { Calendar, Clock, MapPin, User, X, Link } from 'lucide-vue-next'
import logo from '@/img/logo.svg'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()

const training = ref(null)
const loading = ref(true)
const error = ref(null)
const user = ref(null)

const trainingUuid = computed(() => route.params.uuid)
const isAuthenticated = computed(() => authStore.isAuthenticated)
const isGuest = computed(() => authStore.user?.is_guest ?? false)

const participants = computed(() => training.value?.participants || [])

const registeredCount = computed(() => {
  return (participants.value || []).filter((p) => !p.is_guest || p.is_active !== false).length
})

const sortedParticipants = computed(() => {
  // Сортируем: сначала админы, потом пользователи, потом гости
  return [...participants.value].sort((a, b) => {
    const roleA = getParticipantRole(a)
    const roleB = getParticipantRole(b)
    const order = { admin: 0, user: 1, guest: 2 }
    return order[roleA] - order[roleB]
  })
})

onMounted(async () => {
  // Проверяем авторизацию
  if (authStore.isLoading) {
    await authStore.checkAuth()
  }

  if (!authStore.isAuthenticated) {
    // Редирект на страницу авторизации с redirect параметром
    router.push(`/login?redirect=/guest/training/${trainingUuid.value}`)
    return
  }

  user.value = authStore.user

  // Если пользователь не гость и это не его тренировка - показываем полную версию
  if (!isGuest.value) {
    // Проверяем, имеет ли пользователь доступ к этой тренировке
    const userTrainingUuid = authStore.user.training_uuid
    if (userTrainingUuid && userTrainingUuid !== trainingUuid.value) {
      // Это не его тренировка, но он не гость - показываем полную версию
      router.push(`/dashboard/calendar?uuid=${trainingUuid.value}`)
      return
    }
  }

  loadTraining()
})

const loadTraining = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch(`/api/trainings/${trainingUuid.value}`, {
      credentials: 'include',
    })

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('У вас нет доступа к этой тренировке')
      } else if (response.status === 404) {
        throw new Error('Тренировка не найдена')
      } else {
        throw new Error('Ошибка загрузки данных')
      }
    }

    const result = await response.json()
    training.value = result.training
  } catch (err) {
    console.error('Error loading training:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const unregister = async () => {
  try {
    const response = await fetch(`/api/guest/leave/${trainingUuid.value}`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()

    if (response.ok && result.success) {
      notificationsStore.success('Вы успешно отписались от тренировки')
      loadTraining()
    } else {
      notificationsStore.error(result.detail || 'Ошибка отписки')
    }
  } catch (err) {
    console.error('Error unregistering:', err)
    notificationsStore.error('Ошибка отписки от тренировки')
  }
}

const shareLink = () => {
  const url = `${window.location.origin}/guest/training/${trainingUuid.value}`
  navigator.clipboard
    .writeText(url)
    .then(() => {
      notificationsStore.success('Ссылка скопирована в буфер обмена')
    })
    .catch(() => {
      notificationsStore.error('Не удалось скопировать ссылку')
    })
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const [year, month, day] = dateStr.split('-')
  const date = new Date(year, month - 1, day)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    weekday: 'long',
  })
}

const getInitials = (participant) => {
  const first = participant.first_name?.[0] || ''
  const last = participant.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}

const getParticipantKey = (participant) => {
  if (participant.is_guest) {
    return `guest_${participant.telegram_id}`
  }
  return `user_${participant.user_telegram_id}`
}

const getParticipantRole = (participant) => {
  // Проверяем is_admin для пользователей
  if (participant.is_admin) {
    return 'admin'
  }
  // Проверяем is_guest для гостей
  if (participant.is_guest) {
    return 'guest'
  }
  return 'user'
}

const getParticipantRoleText = (participant) => {
  const role = getParticipantRole(participant)
  const roleTexts = {
    admin: 'Администратор',
    user: 'Участник',
    guest: 'Гость',
  }
  return roleTexts[role] || 'Участник'
}
</script>

<style scoped>
/* Дополнительные стили если нужны */
</style>
