<template>
  <div class="space-y-4">
    <div v-if="settingsStore.activePolls.length > 0" class="divide-y divide-gray-100">
      <div v-for="poll in settingsStore.activePolls" :key="poll.id" class="py-4 flex items-center justify-between">
        <div>
          <strong class="text-gray-900">Опрос #{{ poll.id.slice(0, 8) }}</strong>
          <p class="text-sm text-gray-500 mt-1">Chat: {{ poll.chat_id }}</p>
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

onMounted(async () => {
  await settingsStore.loadActivePolls()
})
</script>
