<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <div v-if="settingsStore.activePolls.length > 0" class="divide-y divide-gray-100">
      <div v-for="poll in settingsStore.activePolls" :key="poll.id" class="py-4 flex items-center justify-between gap-4">
        <div class="flex-1">
          <strong class="text-gray-900">Опрос #{{ poll.id.slice(0, 8) }}</strong>
          <p class="text-sm text-gray-500 mt-1">Chat: {{ poll.chat_id }}</p>
          <p class="text-sm text-gray-500">Message ID: {{ poll.message_id }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleStop(poll)"
            class="px-4 py-2 text-sm font-medium text-white bg-yellow-600 rounded hover:bg-yellow-700 transition-colors"
          >
            Остановить
          </button>
          <button
            @click="handleDelete(poll)"
            class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 transition-colors"
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

const settingsStore = useSettingsStore()

const handleStop = async (poll) => {
  if (!confirm(`Остановить опрос #${poll.id.slice(0, 8)}?`)) {
    return
  }

  const success = await settingsStore.stopPoll(poll.id)
  if (success) {
    await settingsStore.loadActivePolls()
  } else {
    alert('Ошибка при остановке опроса')
  }
}

const handleDelete = async (poll) => {
  if (!confirm(`Удалить опрос #${poll.id.slice(0, 8)}?`)) {
    return
  }

  const success = await settingsStore.deletePoll(poll.id)
  if (success) {
    await settingsStore.loadActivePolls()
  } else {
    alert('Ошибка при удалении опроса')
  }
}

onMounted(async () => {
  await settingsStore.loadActivePolls()
})
</script>
