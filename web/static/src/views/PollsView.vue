<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Активные опросы</h1>

    <div v-if="settingsStore.activePolls.length > 0" class="divide-y divide-gray-100">
      <div v-for="poll in settingsStore.activePolls" :key="poll.id" class="py-4 flex items-center justify-between gap-4">
        <div class="flex-1">
          <!-- Заголовок с бейджем статуса -->
          <div class="flex items-center gap-2 mb-1">
            <p v-if="poll.name" class="text-base font-semibold text-gray-900">
              {{ poll.name }}
            </p>
            <p v-else class="text-base font-semibold text-gray-900">
              Опрос #{{ poll.id.slice(0, 8) }}
            </p>
            <span
              class="px-2 py-0.5 rounded text-xs font-medium"
              :class="poll.status === 'stopped' ? 'bg-gray-100 text-gray-700' : 'bg-teal-100 text-teal-700'"
            >
              {{ poll.status === 'stopped' ? 'Остановлен' : 'Активен' }}
            </span>
          </div>
          
          <!-- Дата, время, место -->
          <div class="text-sm text-gray-500 space-y-1">
            <p v-if="poll.training_date" class="flex items-center gap-2">
              <Calendar class="w-4 h-4" />
              <span>{{ formatDate(poll.training_date) }}</span>
            </p>
            <p v-if="poll.training_time" class="flex items-center gap-2">
              <Clock class="w-4 h-4" />
              <span>{{ poll.training_time }}</span>
            </p>
            <p v-if="poll.location" class="flex items-center gap-2">
              <MapPin class="w-4 h-4" />
              <span>{{ poll.location }}</span>
            </p>
          </div>
          
          <!-- Chat и Topic -->
          <p class="text-xs text-gray-400 mt-2">
            Chat: {{ poll.chat_id }}
            <span v-if="poll.message_thread_id"> (топик {{ poll.message_thread_id }})</span>
          </p>
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="poll.status !== 'stopped'"
            @click="handleStop(poll)"
            class="px-4 py-2 text-sm font-medium transition-colors text-yellow-600 hover:text-yellow-700 bg-transparent hover:bg-yellow-50 rounded"
          >
            Остановить
          </button>
          <button
            @click="handleDelete(poll)"
            class="px-4 py-2 text-sm font-medium transition-colors text-red-600 hover:text-red-700 bg-transparent hover:bg-red-50 rounded"
          >
            Удалить
          </button>
        </div>
      </div>
    </div>
    <div v-else class="text-gray-500 text-center py-8">
      Нет активных опросов
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useConfirmStore } from '@/stores/confirm'
import { useNotificationsStore } from '@/stores/notifications'
import { Calendar, Clock, MapPin } from 'lucide-vue-next'

const settingsStore = useSettingsStore()
const confirmStore = useConfirmStore()
const notificationsStore = useNotificationsStore()

const handleStop = async (poll) => {
  const confirmed = await confirmStore.info(`Остановить опрос "${poll.name || poll.id.slice(0, 8)}"?`)
  if (!confirmed) return

  const success = await settingsStore.stopPoll(poll.id)
  if (success) {
    await settingsStore.loadActivePolls()
    notificationsStore.success('Опрос остановлен')
  } else {
    notificationsStore.error('Ошибка при остановке опроса')
  }
}

const handleDelete = async (poll) => {
  const confirmed = await confirmStore.danger(`Удалить опрос "${poll.name || poll.id.slice(0, 8)}"?`)
  if (!confirmed) return

  const success = await settingsStore.deletePoll(poll.id)
  if (success) {
    await settingsStore.loadActivePolls()
    notificationsStore.success('Опрос удалён')
  } else {
    notificationsStore.error('Ошибка при удалении опроса')
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
  return date.toLocaleDateString('ru-RU', options)
}

onMounted(async () => {
  await settingsStore.loadActivePolls()
})
</script>
