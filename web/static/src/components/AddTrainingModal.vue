<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click="$emit('close')">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md" @click.stop>
      <!-- Заголовок -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white">
        <h3 class="text-lg font-semibold text-gray-900">Добавить тренировку</h3>
        <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100">
          ✕
        </button>
      </div>

      <!-- Форма -->
      <div class="p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Дата</label>
          <input
            v-model="formData.training_date"
            type="date"
            :min="today"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Время</label>
          <input
            v-model="formData.training_time"
            type="text"
            placeholder="18:00 - 20:00"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Название</label>
          <input
            v-model="formData.name"
            type="text"
            placeholder="Например: Дополнительная тренировка"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Chat ID</label>
          <input
            v-model="formData.chat_id"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Topic ID (опционально)</label>
          <input
            v-model="formData.topic_id"
            type="number"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        </div>
      </div>

      <!-- Кнопки -->
      <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-2">
        <button
          @click="$emit('close')"
          class="px-4 py-2 rounded font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
        >
          Отмена
        </button>
        <button
          @click="handleSubmit"
          class="px-4 py-2 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700"
        >
          Добавить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  date: {
    type: String,
    default: ''
  },
  defaultChatId: {
    type: String,
    default: ''
  },
  defaultTopicId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['close', 'add'])

// Сегодняшняя дата для минимальной даты
const today = new Date().toISOString().split('T')[0]

const formData = ref({
  training_date: props.date || '',
  training_time: '',
  name: '',
  chat_id: props.defaultChatId || '',
  topic_id: props.defaultTopicId !== undefined ? props.defaultTopicId : null
})

const handleSubmit = () => {
  if (!formData.value.training_date || !formData.value.training_time || !formData.value.name || !formData.value.chat_id) {
    alert('Заполните обязательные поля')
    return
  }

  emit('add', {
    ...formData.value,
    topic_id: formData.value.topic_id ? parseInt(formData.value.topic_id) : null
  })
}
</script>
