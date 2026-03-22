<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Записи на тренировки и игры</h1>

    <!-- Фильтр по дате -->
    <div class="flex flex-wrap gap-4 mb-6">
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium text-gray-700">С даты</label>
        <input
          v-model="startDate"
          type="date"
          class="h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
          @change="loadTrainings"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium text-gray-700">По дату</label>
        <input
          v-model="endDate"
          type="date"
          class="h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
          @change="loadTrainings"
        />
      </div>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-500">Загрузка...</div>

    <div v-else-if="allItems.length === 0" class="text-center py-8 text-gray-500">
      Нет записей за выбранный период
    </div>

    <div v-else class="space-y-6">
      <!-- Группировка по датам -->
      <div
        v-for="(group, date) in groupedItems"
        :key="date"
        class="border border-gray-200 rounded-lg overflow-hidden"
      >
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <!-- Заголовок для игр -->
          <div v-if="group[0].type === 'game'" class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700">
              Игра
            </span>
            <h3 class="font-semibold text-gray-900">
              {{ group[0].game_name }}
              <span class="text-gray-500 font-normal">
                {{ formatShortDate(group[0].date) }}, {{ group[0].start_time }}
                <span v-if="group[0].location">, {{ group[0].location }}</span>
                <span v-if="group[0].opponent">, vs {{ group[0].opponent }}</span>
              </span>
            </h3>
          </div>

          <!-- Заголовок для тренировок -->
          <div v-else class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-xs font-medium bg-teal-100 text-teal-700">
              Тренировка
            </span>
            <h3 class="font-semibold text-gray-900">
              {{ group[0].training_name || group[0].schedule_name }}
              <span class="text-gray-500 font-normal">
                {{ formatShortDate(date.split('_')[0]) }}
                <span v-if="group[0].time">, {{ group[0].time }}</span>
                <span v-if="group[0].location">, {{ group[0].location }}</span>
              </span>
            </h3>
          </div>
        </div>
        <div class="divide-y divide-gray-100">
          <div
            v-for="item in group"
            :key="item.id"
            class="px-4 py-3 flex items-center justify-between"
          >
            <div>
              <!-- Имя участника -->
              <p class="font-medium text-gray-900">
                {{ item.first_name }} {{ item.last_name || '' }}
                <span v-if="item.username" class="text-gray-400 font-normal"
                  >@{{ item.username }}</span
                >
              </p>

              <!-- Статус только для тренировок -->
              <div
                v-if="item.type === 'training' && item.status"
                class="flex items-center gap-2 mt-1"
              >
                <span
                  class="px-2 py-0.5 rounded text-xs font-medium"
                  :class="
                    item.status === 'registered'
                      ? 'bg-teal-100 text-teal-700'
                      : 'bg-yellow-100 text-yellow-700'
                  "
                >
                  {{ item.status === 'registered' ? 'Записан' : 'Резерв' }}
                </span>
              </div>
            </div>
            <!-- Кнопка удаления для админа -->
            <button
              @click="removeUser(item)"
              class="w-8 h-8 flex items-center justify-center rounded hover:bg-red-50 text-red-500 transition-colors"
              title="Удалить участника"
            >
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { X } from 'lucide-vue-next'
import { useNotificationsStore } from '@/stores/notifications'
import { useConfirmStore } from '@/stores/confirm'

const startDate = ref('')
const endDate = ref('')
const allItems = ref([])
const loading = ref(false)

const notificationsStore = useNotificationsStore()
const confirmStore = useConfirmStore()

onMounted(() => {
  // Устанавливаем даты по умолчанию (текущий месяц)
  const now = new Date()
  startDate.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
  endDate.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

  loadTrainings()
})

const loadTrainings = async () => {
  loading.value = true

  try {
    // Загружаем тренировки и игры параллельно
    const [trainingsResponse, gamesResponse] = await Promise.all([
      fetch(`/api/admin/trainings?start_date=${startDate.value}&end_date=${endDate.value}`, {
        credentials: 'include',
      }),
      fetch(`/api/admin/games/signups?start_date=${startDate.value}&end_date=${endDate.value}`, {
        credentials: 'include',
      }),
    ])

    const trainingsData = await trainingsResponse.json()
    const gamesData = await gamesResponse.json()

    // Объединяем с указанием типа
    const items = [
      ...(trainingsData.trainings || []).map((t) => ({ ...t, type: 'training' })),
      ...(gamesData.signups || []).map((g) => ({ ...g, type: 'game' })),
    ]

    // Фильтруем прошедшие
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    const filteredItems = items.filter((item) => {
      const itemDate = new Date(item.training_date || item.date)
      return itemDate >= today
    })

    // Сортируем по дате и времени
    filteredItems.sort((a, b) => {
      const dateA = a.training_date || a.date
      const dateB = b.training_date || b.date
      const timeA = a.time || a.start_time
      const timeB = b.time || b.start_time
      return (dateA + ' ' + timeA).localeCompare(dateB + ' ' + timeB)
    })

    allItems.value = filteredItems
  } catch (error) {
    console.error('Error loading trainings:', error)
  } finally {
    loading.value = false
  }
}

const groupedItems = computed(() => {
  const groups = {}

  allItems.value.forEach((item) => {
    // Для тренировок и игр используем разные поля даты
    const date = item.training_date || item.date
    const chatId = item.chat_id || ''
    const gameId = item.game_id || ''

    // Для игр группируем по game_id, для тренировок по date+chat_id
    // Ключ сортировки начинается с даты
    const key = item.type === 'game' ? `${date}_game_${gameId}` : `${date}_${chatId}`

    if (!groups[key]) {
      groups[key] = []
    }
    groups[key].push({
      ...item,
      time: item.training_time || item.start_time,
    })
  })

  // Сортируем даты
  const sorted = {}
  Object.keys(groups)
    .sort()
    .forEach((key) => {
      sorted[key] = groups[key]
    })

  return sorted
})

const formatDate = (dateKey) => {
  // Для игр ключ содержит 'game_'
  if (dateKey.includes('_game_')) {
    const date = dateKey.split('_game_')[0]
    const d = new Date(date)
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
    return d.toLocaleDateString('ru-RU', options)
  }

  // Для тренировок - ключ может быть формата YYYY-MM-DD_chat_id или timestamp_chat_id
  const parts = dateKey.split('_')
  let date = parts[0]

  // Если это timestamp (содержит точку), конвертируем
  if (date.includes('.')) {
    const d = new Date(date)
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
    return d.toLocaleDateString('ru-RU', options)
  }

  // Иначе это YYYY-MM-DD
  const d = new Date(date)
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
  return d.toLocaleDateString('ru-RU', options)
}

const formatShortDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  return `${day}.${month}.${year}`
}

const removeUser = async (item) => {
  const name = item.first_name + (item.last_name ? ' ' + item.last_name : '')
  const date = item.training_date || item.date

  let confirmed
  if (item.type === 'game') {
    confirmed = await confirmStore.danger(`Удалить ${name} из игры ${date}?`)
  } else {
    confirmed = await confirmStore.danger(`Удалить ${name} из тренировки ${date}?`)
  }
  if (!confirmed) return

  try {
    let response
    if (item.type === 'game') {
      // Удаление из игры
      response = await fetch(`/api/games/${item.game_id}/unregister`, {
        method: 'POST',
        credentials: 'include',
      })
    } else {
      // Удаление из тренировки
      response = await fetch(
        `/api/admin/calendar/remove-user/${item.uuid}/${item.user_telegram_id}`,
        {
          method: 'DELETE',
          credentials: 'include',
        },
      )
    }

    const result = await response.json()

    if (response.ok && result.success) {
      // Перезагружаем список
      await loadTrainings()
      notificationsStore.success('Пользователь удалён')
    } else {
      notificationsStore.error(result.detail || 'Ошибка удаления участника')
    }
  } catch (error) {
    console.error('Error removing user:', error)
    notificationsStore.error('Ошибка удаления участника')
  }
}
</script>
