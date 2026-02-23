<template>
  <div class="bg-white rounded shadow p-6">
    <div class="flex flex-col gap-6">
      <div class="flex flex-col gap-2">
        <label class="block text-sm font-medium text-gray-700">Добавить администратора</label>
        <div class="flex gap-2">
          <input
            v-model="newAdminId"
            type="number"
            class="flex-1 px-4 py-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            placeholder="Telegram ID"
          />
          <button @click="handleAdd" class="px-6 py-3 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700">
            Добавить
          </button>
        </div>
      </div>

      <div v-if="adminIds.length > 0" class="space-y-2">
        <div v-for="id in adminIds" :key="id" class="flex items-center justify-between py-3 px-4 bg-gray-50 rounded">
          <span class="font-mono text-sm text-gray-700">ID: {{ id }}</span>
          <div class="flex items-center gap-2">
            <span class="px-3 py-1 rounded text-xs font-medium bg-green-100 text-green-700">Админ</span>
            <button @click="handleRemove" class="w-8 h-8 flex items-center justify-center rounded hover:bg-red-50 text-red-500 transition-colors">
              ✕
            </button>
          </div>
        </div>
      </div>
      <div v-else class="text-gray-500 text-center py-8">
        Нет администраторов
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()
const newAdminId = ref('')

const adminIds = computed(() => settingsStore.adminIds)

const handleAdd = async () => {
  if (newAdminId.value) {
    const success = await settingsStore.addAdminId(parseInt(newAdminId.value))
    if (success) {
      newAdminId.value = ''
    } else {
      alert('Ошибка добавления администратора')
    }
  }
}

const handleRemove = async () => {
  const id = adminIds.value[0]
  if (id && confirm(`Удалить администратора ${id}?`)) {
    const success = await settingsStore.removeAdminId(id)
    if (!success) {
      alert('Ошибка удаления')
    }
  }
}
</script>
