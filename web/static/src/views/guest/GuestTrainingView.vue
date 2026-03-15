<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="max-w-3xl mx-auto px-4 py-4">
        <div class="flex items-center gap-3">
          <img :src="logo" alt="Team R Logo" class="w-10 h-10" />
          <div>
            <h1 class="text-xl font-bold text-gray-900">Team R</h1>
            <p class="text-xs text-gray-500">Волейбольные тренировки</p>
          </div>
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
            <div v-if="getTimeDisplay()" class="flex items-center gap-2">
              <Clock class="w-4 h-4" />
              <span>{{ getTimeDisplay() }}</span>
            </div>
            <div v-if="training.location" class="flex items-center gap-2">
              <MapPin class="w-4 h-4" />
              <span>{{ training.location }}</span>
            </div>
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
                  <Shield
                    v-if="getParticipantRole(participant) === 'admin'"
                    class="w-4 h-4 text-purple-600 flex-shrink-0"
                    title="Администратор"
                  />
                  <User
                    v-else-if="getParticipantRole(participant) === 'guest'"
                    class="w-4 h-4 text-blue-600 flex-shrink-0"
                    title="Гость"
                  />
                  <BadgeCheck
                    v-else
                    class="w-4 h-4 text-teal-600 flex-shrink-0"
                    title="Участник"
                  />
                  <span class="text-xs text-gray-500">
                    {{ getParticipantRoleText(participant) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-8 text-gray-500">Пока никто не записался</div>
        </div>

        <!-- Кнопка записаться/отписаться -->
        <div class="px-6 py-4 border-t border-gray-100 bg-gray-50">
          <button
            v-if="isRegistered"
            @click="unregister"
            class="w-full text-center text-red-600 hover:text-red-700 transition-colors font-medium text-sm"
          >
            Отписаться
          </button>
          <button
            v-else
            @click="register"
            class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors font-medium"
          >
            <Calendar class="w-5 h-5" />
            Записаться на тренировку
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
import { Calendar, Clock, MapPin, X, Shield, BadgeCheck, User } from 'lucide-vue-next'
import logo from '@/img/logo.svg'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()

const training = ref(null)
const loading = ref(true)
const error = ref(null)
const user = ref(null)
const userTrainings = ref([])

const trainingUuid = computed(() => route.params.uuid)
const isAuthenticated = computed(() => authStore.isAuthenticated)
const isGuest = computed(() => authStore.user?.is_guest ?? false)

const participants = computed(() => training.value?.registrations || [])

const registeredCount = computed(() => {
  return (participants.value || []).filter((p) => !p.is_guest || p.is_active !== false).length
})

// Проверяем, записан ли текущий пользователь
const isRegistered = computed(() => {
  if (!user.value || !participants.value) return false
  const userId = user.value.telegram_id
  return participants.value.some(p => p.user_telegram_id === userId || p.telegram_id === userId)
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
  // Загружаем данные пользователя через API для гостей
  try {
    const response = await fetch('/api/guest/me', {
      credentials: 'include',
    })
    if (response.ok) {
      const guestData = await response.json()
      user.value = guestData
      userTrainings.value = guestData.trainings || []
      authStore.setUser(guestData)
    }
  } catch (err) {
    console.error('Error loading user data:', err)
  }

  // Затем загружаем данные тренировки
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
      // Обновляем список тренировок
      userTrainings.value = userTrainings.value.filter(t => t.training_uuid !== trainingUuid.value)
      loadTraining()
    } else {
      notificationsStore.error(result.detail || 'Ошибка отписки')
    }
  } catch (err) {
    console.error('Error unregistering:', err)
    notificationsStore.error('Ошибка отписки от тренировки')
  }
}

const register = async () => {
  try {
    // Получаем данные пользователя из authStore
    const userData = authStore.user

    if (!userData) {
      notificationsStore.error('Пользователь не авторизован')
      return
    }

    const response = await fetch(`/api/guest/join/${trainingUuid.value}`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        telegram_id: userData.telegram_id || userData.id,
        first_name: userData.first_name,
        last_name: userData.last_name || '',
        username: userData.username || '',
        photo_url: userData.photo_url || '',
      }),
    })

    const result = await response.json()

    if (response.ok && result.success) {
      notificationsStore.success('Вы успешно записались на тренировку')
      // Обновляем список тренировок
      if (!userTrainings.value.find(t => t.training_uuid === trainingUuid.value)) {
        userTrainings.value.push({ training_uuid: trainingUuid.value })
      }
      // Перезагружаем данные тренировки
      loadTraining()
    } else {
      notificationsStore.error(result.detail || 'Ошибка записи')
    }
  } catch (err) {
    console.error('Error registering:', err)
    notificationsStore.error('Ошибка записи на тренировку')
  }
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

const getTimeDisplay = () => {
  if (!training.value) return ''
  
  // Для игр (event_type === 'game') используем только start_time
  if (training.value.event_type === 'game') {
    return training.value.start_time || training.value.time || ''
  }
  
  // Для тренировок используем time (который уже нормализован)
  return training.value.time || training.value.start_time || ''
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
