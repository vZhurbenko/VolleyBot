<template>
  <div class="space-y-4">
    <div class="pb-4 border-b border-gray-100">
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Добавить администратора</label>
        <div class="flex gap-2">
          <input 
            v-model="newAdminId" 
            type="number" 
            class="flex-1 h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-colors"
            placeholder="Telegram ID"
          />
          <button @click="handleAdd" class="h-11 px-6 rounded font-medium transition-colors bg-gray-900 text-white hover:bg-gray-800 whitespace-nowrap">
            Добавить
          </button>
        </div>
      </div>
    </div>
    
    <div class="space-y-2">
      <div v-for="id in adminIds" :key="id" class="flex items-center justify-between py-3 px-4 bg-gray-50 rounded">
        <span class="font-mono text-sm text-gray-700">ID: {{ id }}</span>
        <div class="flex items-center gap-2">
          <span class="px-3 py-1 rounded text-xs font-medium bg-teal-100 text-teal-700">Админ</span>
          <button @click="$emit('remove', id)" class="w-8 h-8 flex items-center justify-center rounded hover:bg-red-50 text-red-500 transition-colors">
            ✕
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  adminIds: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['add', 'remove'])

const newAdminId = ref('')

const handleAdd = () => {
  if (newAdminId.value) {
    emit('add', parseInt(newAdminId.value))
    newAdminId.value = ''
  }
}
</script>
