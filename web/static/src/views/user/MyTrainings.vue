<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Мои тренировки и игры</h1>

    <div v-if="loading" class="text-center py-8 text-gray-500">
      Загрузка...
    </div>

    <div v-else-if="items.length === 0" class="text-center py-8 text-gray-500">
      Вы ещё не записаны ни на одну тренировку или игру
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="item in items"
        :key="item.id"
        class="flex items-center justify-between p-4 bg-gray-50 rounded"
      >
        <div class="flex-1">
          <!-- Тип и название -->
          <div class="flex items-center gap-2 mb-1">
            <span
              class="px-2 py-0.5 rounded text-xs font-medium"
              :class="item.type === 'game' ? 'bg-purple-100 text-purple-700' : 'bg-teal-100 text-teal-700'"
            >
              {{ item.type === 'game' ? 'Игра' : 'Тренировка' }}
            </span>
            <p v-if="item.training_name || item.schedule_name || item.name" class="text-base font-semibold text-gray-900">
              {{ item.training_name || item.schedule_name || item.name }}
            </p>
          </div>
          
          <!-- Дата и статус -->
          <div class="flex items-center gap-2 mb-1">
            <span class="text-lg font-semibold text-gray-900">
              {{ formatDate(item.training_date || item.date) }}
            </span>
            <span
              v-if="item.status || item.signup_status"
              class="px-2 py-0.5 rounded text-xs font-medium"
              :class="(item.status || item.signup_status) === 'registered' ? 'bg-teal-100 text-teal-700' : 'bg-yellow-100 text-yellow-700'"
            >
              {{ (item.status || item.signup_status) === 'registered' ? 'Записан' : 'Резерв' }}
            </span>
          </div>
          
          <!-- Время и место -->
          <p v-if="item.training_time" class="text-sm text-gray-500 flex items-center gap-1">
            <Clock class="w-4 h-4" /> {{ item.training_time }}
          </p>
          <p v-else-if="item.start_time && item.end_time" class="text-sm text-gray-500 flex items-center gap-1">
            <Clock class="w-4 h-4" /> {{ item.start_time }} - {{ item.end_time }}
          </p>
          <p v-if="item.location" class="text-sm text-gray-500">
            📍 {{ item.location }}
          </p>
        </div>

        <button
          v-if="item.type === 'training'"
          @click="unregister(item)"
          class="px-4 py-2 rounded font-medium transition-colors text-red-600 hover:text-red-700 bg-transparent"
        >
          Выписаться
        </button>
        <button
          v-else
          @click="unregisterFromGame(item)"
          class="px-4 py-2 rounded font-medium transition-colors text-red-600 hover:text-red-700 bg-transparent"
        >
          Выписаться
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { useConfirmStore } from '@/stores/confirm'
import { Clock } from 'lucide-vue-next'

const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const confirmStore = useConfirmStore()

const items = ref([])
const loading = ref(false)

onMounted(() => {
  loadItems()
})

const loadItems = async () => {
  loading.value = true

  try {
    const response = await fetch('/api/user/my-trainings', {
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error('Failed to load items')
    }

    const data = await response.json()
    items.value = data.items || []
  } catch (error) {
    console.error('Error loading items:', error)
  } finally {
    loading.value = false
  }
}

const unregister = async (training) => {
  const confirmed = await confirmStore.info('Выписаться с тренировки?')
  if (!confirmed) return

  try {
    const response = await fetch('/api/user/calendar/unregister', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        training_date: training.training_date,
        training_time: training.training_time,
        chat_id: training.chat_id
      })
    })

    const result = await response.json()

    if (response.ok && result.success) {
      loadItems()
      notificationsStore.success('Вы успешно выписались с тренировки')
    } else {
      notificationsStore.error(result.detail || 'Ошибка отписки')
    }
  } catch (error) {
    console.error('Error unregistering:', error)
    notificationsStore.error('Ошибка отписки от тренировки')
  }
}

const unregisterFromGame = async (game) => {
  const confirmed = await confirmStore.info('Выписаться с игры?')
  if (!confirmed) return

  try {
    const response = await fetch(`/api/games/${game.id}/unregister`, {
      method: 'POST',
      credentials: 'include'
    })

    const result = await response.json()

    if (response.ok && result.success) {
      loadItems()
      notificationsStore.success('Вы успешно выписались с игры')
    } else {
      notificationsStore.error(result.detail || 'Ошибка отписки')
    }
  } catch (error) {
    console.error('Error unregistering from game:', error)
    notificationsStore.error('Ошибка отписки от игры')
  }
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
  return date.toLocaleDateString('ru-RU', options)
}
</script>
