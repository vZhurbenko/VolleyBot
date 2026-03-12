<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Календарь тренировок</h1>

    <div v-if="loading" class="text-center py-8 text-gray-500">Загрузка...</div>

    <Calendar
      v-if="!loading"
      :key="`calendar-${currentYear}-${currentMonth}`"
      :year="currentYear"
      :month="currentMonth"
      :trainings="trainings"
      :games="games"
      :is-admin="authStore.isAdmin"
      @click-training="openTrainingModal"
      @click-game="openGameModal"
      @update-month="updateMonth"
      @add-training="openAddTrainingModal"
    />

    <!-- Модалка тренировки -->
    <TrainingModal
      v-if="selectedTraining"
      :training="selectedTraining"
      @close="closeTrainingModal"
      @register="registerForTraining"
      @unregister="unregisterFromTraining"
      @remove-training="removeOneTimeTraining"
      @remove-user="removeUserFromTraining"
    />

    <!-- Модалка игры -->
    <GameModal
      v-if="selectedGame"
      :game="selectedGame"
      @close="closeGameModal"
      @update-game="updateGameSignup"
    />

    <!-- Модалка добавления тренировки -->
    <AddTrainingModal
      v-if="showAddModal"
      :date="selectedDate"
      :default-chat-id="defaultChatId"
      :default-topic-id="defaultTopicId"
      @close="closeAddTrainingModal"
      @add="addOneTimeTraining"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useConfirmStore } from '@/stores/confirm'
import Calendar from '@/components/Calendar.vue'
import TrainingModal from '@/components/TrainingModal.vue'
import AddTrainingModal from '@/components/AddTrainingModal.vue'
import GameModal from '@/components/GameModal.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const confirmStore = useConfirmStore()

const trainings = ref([])
const games = ref([])
const selectedTraining = ref(null)
const selectedGame = ref(null)
const loading = ref(false)

// Для добавления тренировки
const showAddModal = ref(false)
const selectedDate = ref('')
const defaultChatId = ref('')
const defaultTopicId = ref(null)

const now = new Date()
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth() + 1)

// Обновляем из query параметров при загрузке
if (route.query.year) {
  currentYear.value = parseInt(route.query.year) || now.getFullYear()
}
if (route.query.month) {
  currentMonth.value = parseInt(route.query.month) || now.getMonth() + 1
}

// Следим за изменениями query параметров и обновляем календарь
watch(
  () => [route.query.year, route.query.month],
  ([year, month]) => {
    const newYear = parseInt(year) || now.getFullYear()
    const newMonth = parseInt(month) || now.getMonth() + 1

    // Обновляем только если значения изменились
    if (newYear !== currentYear.value || newMonth !== currentMonth.value) {
      currentYear.value = newYear
      currentMonth.value = newMonth
      loadCalendar()
    }
  },
  { immediate: false },
)

onMounted(async () => {
  // Ждём загрузки auth store
  if (authStore.isLoading) {
    await authStore.checkAuth()
  }

  // Проверяем авторизацию
  if (!authStore.isAuthenticated) {
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath))
    return
  }

  await Promise.all([loadCalendar(), settingsStore.loadTemplate()])

  // Загружаем значения по умолчанию из шаблона
  const template = settingsStore.template
  if (template) {
    defaultChatId.value = template.default_chat_id || ''
    defaultTopicId.value =
      template.default_topic_id !== undefined ? template.default_topic_id : null
  }
})

const loadCalendar = async () => {
  loading.value = true

  try {
    const response = await fetch(
      `/api/user/calendar?year=${currentYear.value}&month=${currentMonth.value}`,
    )

    if (!response.ok) {
      throw new Error('Failed to load calendar')
    }

    const data = await response.json()
    trainings.value = data.trainings || []
    games.value = data.games || []

    // Проверяем, есть ли параметр для открытия тренировки по UUID
    if (route.query.training) {
      openTrainingByUuid(route.query.training)
    }

    // Проверяем, есть ли параметры для открытия конкретной тренировки
    if (route.query.date && route.query.chat_id && route.query.time) {
      openTrainingByParams()
    }

    // Проверяем, есть ли параметр для открытия игры
    if (route.query.game_id) {
      openGameByParams()
    }
  } catch (error) {
    console.error('Error loading calendar:', error)
  } finally {
    loading.value = false
  }
}

const openTrainingByUuid = (trainingUuid) => {
  console.log('[CalendarView] openTrainingByUuid:', trainingUuid)
  
  // Сначала ищем в тренировках
  let training = trainings.value.find((t) => t.uuid === trainingUuid)
  if (training) {
    console.log('[CalendarView] Найдена тренировка:', training)
    selectedTraining.value = { ...training }
    return
  }
  
  // Если не найдено, ищем в играх
  let game = games.value.find((g) => g.uuid === trainingUuid)
  if (game) {
    console.log('[CalendarView] Найдена игра:', game)
    selectedGame.value = { ...game }
  } else {
    console.log('[CalendarView] Не найдено ничего')
    notificationsStore.error('Тренировка не найдена')
  }
}

// Закрываем модалку при изменении URL (если параметр training исчез)
watch(() => route.query.training, (newVal) => {
  if (!newVal) {
    selectedTraining.value = null
  }
})

// Закрываем модалку игры при изменении URL (если параметр training исчез)
// Для игр используется тот же параметр training, а не game_id
watch(() => route.query.training, (newVal) => {
  if (!newVal) {
    selectedGame.value = null
  }
})

const openTrainingByParams = () => {
  const targetDate = route.query.date
  const targetChatId = route.query.chat_id
  const targetTime = decodeURIComponent(route.query.time || '')

  const training = trainings.value.find(
    (t) => t.date === targetDate && t.chat_id === targetChatId && t.time === targetTime,
  )

  if (training) {
    selectedTraining.value = { ...training }
  } else {
    notificationsStore.error('Тренировка не найдена')
  }
}

const openGameByParams = () => {
  const targetGameId = route.query.game_id

  const game = games.value.find((g) => g.id === targetGameId)

  if (game) {
    selectedGame.value = { ...game }
  } else {
    notificationsStore.error('Игра не найдена')
  }
}

// Обновляем query параметры (watch загрузит календарь)
const updateMonth = ({ year, month }) => {
  router.push({
    query: {
      ...route.query,
      year,
      month,
    },
  })
}

const openTrainingModal = (training) => {
  selectedTraining.value = { ...training }
}

const closeTrainingModal = () => {
  selectedTraining.value = null

  // Очищаем query параметры, чтобы модалка не открывалась снова
  router.push({
    query: {
      ...route.query,
      date: undefined,
      chat_id: undefined,
      time: undefined,
    },
  })

  loadCalendar()
}

// Добавление тренировки
const openAddTrainingModal = (dateStr) => {
  selectedDate.value = dateStr || ''
  showAddModal.value = true
}

const closeAddTrainingModal = () => {
  showAddModal.value = false
  selectedDate.value = ''
}

const addOneTimeTraining = async (formData) => {
  try {
    const response = await fetch('/api/admin/calendar/add-training', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(formData),
    })

    const result = await response.json()

    if (response.ok && result.success) {
      closeAddTrainingModal()
      loadCalendar()
      notificationsStore.success('Тренировка добавлена')
    } else {
      notificationsStore.error(result.detail || 'Ошибка добавления')
    }
  } catch (error) {
    console.error('Error adding training:', error)
    notificationsStore.error('Ошибка добавления тренировки')
  }
}

const registerForTraining = async () => {
  if (!selectedTraining.value) return

  try {
    const response = await fetch('/api/user/calendar/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        training_date: selectedTraining.value.date,
        training_time: selectedTraining.value.time,
        chat_id: selectedTraining.value.chat_id,
        topic_id: selectedTraining.value.topic_id,
      }),
    })

    const result = await response.json()

    if (response.ok && result.success) {
      // Обновляем статус в модалке
      selectedTraining.value.user_status = result.status

      // Перезагружаем календарь для обновления списка записавшихся
      await loadCalendar()

      // Находим обновлённую тренировку и обновляем selectedTraining
      const updatedTraining = trainings.value.find(
        (t) =>
          t.date === selectedTraining.value.date &&
          t.time === selectedTraining.value.time &&
          t.chat_id === selectedTraining.value.chat_id,
      )
      if (updatedTraining) {
        selectedTraining.value = { ...updatedTraining }
      }
      notificationsStore.success('Вы записаны на тренировку')
    } else {
      notificationsStore.error(result.detail || 'Ошибка записи')
    }
  } catch (error) {
    console.error('Error registering:', error)
    notificationsStore.error('Ошибка записи на тренировку')
  }
}

const unregisterFromTraining = async () => {
  if (!selectedTraining.value) return

  try {
    const response = await fetch('/api/user/calendar/unregister', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        training_date: selectedTraining.value.date,
        training_time: selectedTraining.value.time,
        chat_id: selectedTraining.value.chat_id,
      }),
    })

    const result = await response.json()

    if (response.ok && result.success) {
      selectedTraining.value.user_status = null
      // Перезагружаем календарь для обновления списка записавшихся
      await loadCalendar()
      // Находим обновлённую тренировку и обновляем selectedTraining
      const updatedTraining = trainings.value.find(
        (t) =>
          t.date === selectedTraining.value.date &&
          t.time === selectedTraining.value.time &&
          t.chat_id === selectedTraining.value.chat_id,
      )
      if (updatedTraining) {
        selectedTraining.value = { ...updatedTraining }
      }
      notificationsStore.success('Вы успешно выписались с тренировки')
    } else {
      notificationsStore.error(result.detail || 'Ошибка отписки')
    }
  } catch (error) {
    console.error('Error unregistering:', error)
    notificationsStore.error('Ошибка отписки от тренировки')
  }
}

const removeOneTimeTraining = async () => {
  if (!selectedTraining.value || !authStore.isAdmin) return

  const confirmed = await confirmStore.danger('Удалить эту тренировку?')
  if (!confirmed) return

  try {
    const trainingId =
      selectedTraining.value.id ||
      `${selectedTraining.value.date}_${selectedTraining.value.time}_${selectedTraining.value.chat_id}`
    const response = await fetch(`/api/admin/calendar/remove-training/${trainingId}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    const result = await response.json()

    if (response.ok && result.success) {
      closeTrainingModal()
      notificationsStore.success('Тренировка удалена')
    } else {
      notificationsStore.error(result.detail || 'Ошибка удаления')
    }
  } catch (error) {
    console.error('Error removing training:', error)
    notificationsStore.error('Ошибка удаления тренировки')
  }
}

const removeUserFromTraining = async (reg) => {
  if (!selectedTraining.value || !authStore.isAdmin) return

  try {
    const response = await fetch(
      `/api/admin/calendar/remove-user/${selectedTraining.value.date}/${encodeURIComponent(selectedTraining.value.time)}/${selectedTraining.value.chat_id}/${reg.user_telegram_id}`,
      {
        method: 'DELETE',
        credentials: 'include',
      },
    )

    const result = await response.json()

    if (response.ok && result.success) {
      // Перезагружаем календарь для обновления данных
      await loadCalendar()
      // Находим обновлённую тренировку
      const updatedTraining = trainings.value.find(
        (t) =>
          t.date === selectedTraining.value.date &&
          t.time === selectedTraining.value.time &&
          t.chat_id === selectedTraining.value.chat_id,
      )
      if (updatedTraining) {
        selectedTraining.value = { ...updatedTraining }
      }
    } else {
      notificationsStore.error(result.detail || 'Ошибка удаления участника')
    }
  } catch (error) {
    console.error('Error removing user:', error)
    notificationsStore.error('Ошибка удаления участника')
  }
}

// Функции для работы с играми
const openGameModal = (game) => {
  selectedGame.value = { ...game }
}

const closeGameModal = () => {
  selectedGame.value = null
  loadCalendar()
}

const updateGameSignup = async () => {
  if (!selectedGame.value) return

  try {
    const response = await fetch(`/api/games/${selectedGame.value.id}/signup`, {
      method: 'POST',
      credentials: 'include',
    })

    const result = await response.json()

    if (response.ok && result.success) {
      notificationsStore.success(
        result.action === 'registered' ? 'Вы записаны на игру' : 'Запись отменена',
      )

      // Обновляем статус в модалке
      const isSignedUp = result.action === 'registered'

      // Перезагружаем календарь для обновления списка записавшихся
      await loadCalendar()

      // Находим обновлённую игру и обновляем selectedGame
      const updatedGame = games.value.find((g) => g.id === selectedGame.value.id)
      if (updatedGame) {
        selectedGame.value = { ...updatedGame }
      }
    } else {
      notificationsStore.error(result.detail || 'Ошибка')
    }
  } catch (error) {
    console.error('Error signing up for game:', error)
    notificationsStore.error('Ошибка записи на игру')
  }
}
</script>
