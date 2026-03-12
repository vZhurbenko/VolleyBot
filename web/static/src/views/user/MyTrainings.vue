<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Мои тренировки и игры</h1>

    <div v-if="loading" class="text-center py-8 text-gray-500">Загрузка...</div>

    <div v-else-if="items.length === 0" class="text-center py-8 text-gray-500">
      Вы ещё не записаны ни на одну тренировку или игру
    </div>

    <div v-else class="space-y-4">
      <!-- Группировка по типу события -->
      <div
        v-for="item in items"
        :key="item.id"
        class="border border-gray-200 rounded-lg overflow-hidden"
      >
        <!-- Заголовок карточки -->
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <div class="flex items-center gap-2">
            <span
              :class="[
                'px-2 py-0.5 rounded text-xs font-medium',
                item.type === 'game'
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-teal-100 text-teal-700',
              ]"
            >
              {{ item.type === 'game' ? 'Игра' : 'Тренировка' }}
            </span>
            <h3 class="font-semibold text-gray-900">
              <template v-if="item.type === 'game'">
                {{ item.name }}
                <span class="text-gray-500 font-normal">
                  {{ formatShortDate(item.date) }}, {{ item.start_time }}
                  <span v-if="item.location">, {{ item.location }}</span>
                  <span v-if="item.opponent">, vs {{ item.opponent }}</span>
                </span>
              </template>
              <template v-else>
                {{ item.training_name || item.schedule_name }}
                <span class="text-gray-500 font-normal">
                  {{ item.training_date ? formatShortDate(item.training_date) + ', ' : '' }}
                  {{ item.training_time }}
                  <span v-if="item.location">, {{ item.location }}</span>
                </span>
              </template>
            </h3>
          </div>
        </div>

        <!-- Тело карточки -->
        <div class="px-4 py-3 flex items-center justify-between">
          <div>
            <p class="font-medium text-gray-900">
              Вы
              <span v-if="authStore.user?.username" class="text-gray-400 font-normal"
                >@{{ authStore.user.username }}</span
              >
            </p>
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

          <button
            @click="item.type === 'game' ? unregisterFromGame(item) : unregister(item)"
            class="px-4 py-2 rounded font-medium transition-colors text-red-600 hover:text-red-700 bg-transparent"
          >
            Выписаться
          </button>
        </div>
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
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to load items')
    }

    const data = await response.json()

    // Фильтруем прошедшие тренировки и игры
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    items.value = (data.items || []).filter((item) => {
      const itemDate = new Date(item.training_date || item.date)
      return itemDate >= today
    })
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
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        training_date: training.training_date,
        training_time: training.training_time,
        chat_id: training.chat_id,
      }),
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
      credentials: 'include',
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

const formatShortDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  return `${day}.${month}.${year}`
}
</script>
