<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click="$emit('close')">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md" @click.stop>
      <!-- Заголовок -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white">
        <h3 class="text-lg font-semibold text-gray-900">
          {{ game ? 'Редактирование игры' : 'Новая игра' }}
        </h3>
        <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Форма -->
      <div class="p-6 space-y-4">
        <form id="game-form" @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Название -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Название игры *
            </label>
            <input
              v-model="form.name"
              type="text"
              required
              placeholder="Товарищеский матч"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <!-- Дата -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Дата проведения *
            </label>
            <input
              v-model="form.date"
              type="date"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <!-- Время начала -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Время начала
            </label>
            <input
              v-model="form.start_time"
              type="time"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <!-- Место проведения -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Место проведения
            </label>
            <input
              v-model="form.location"
              type="text"
              placeholder="СК Звезда"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <!-- Соперник -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Соперник
            </label>
            <input
              v-model="form.opponent"
              type="text"
              placeholder="Команда соперников"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <!-- Chat ID -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Chat ID
            </label>
            <input
              v-model="form.chat_id"
              type="text"
              placeholder="-1001234567890"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <!-- Topic ID -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Topic ID (опционально)
            </label>
            <input
              v-model.number="form.topic_id"
              type="number"
              placeholder="42"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
        </form>
      </div>

      <!-- Кнопки -->
      <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-2">
        <button
          type="submit"
          :disabled="saving"
          form="game-form"
          class="h-11 px-6 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50"
        >
          {{ saving ? 'Сохранение...' : 'Сохранить' }}
        </button>
        <button
          type="button"
          @click="$emit('close')"
          class="h-11 px-6 rounded font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
        >
          Отмена
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps({
  game: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

const form = ref({
  name: '',
  date: '',
  location: '',
  start_time: '',
  opponent: '',
  chat_id: '',
  topic_id: null
})

const saving = ref(false)

// Загрузка настроек по умолчанию
const loadDefaults = async () => {
  try {
    const response = await fetch('/api/user/template')
    if (response.ok) {
      const data = await response.json()
      const template = data.template || {}
      // Используем chat_id из шаблона или дефолтный
      form.value.chat_id = template.default_chat_id || '-1002588984009'
      // Topic ID для игр всегда 382
      form.value.topic_id = 382
    } else {
      // Если не удалось загрузить шаблон, используем дефолтные значения
      form.value.chat_id = '-1002588984009'
      form.value.topic_id = 382
    }
  } catch (error) {
    console.error('Error loading defaults:', error)
    // При ошибке используем дефолтные значения
    form.value.chat_id = '-1002588984009'
    form.value.topic_id = 382
  }
}

onMounted(() => {
  loadDefaults()
})

watch(() => props.game, (newGame) => {
  if (newGame) {
    form.value = {
      name: newGame.name || '',
      date: newGame.date || '',
      location: newGame.location || '',
      start_time: newGame.start_time || '',
      opponent: newGame.opponent || '',
      chat_id: newGame.chat_id || '',
      topic_id: newGame.topic_id !== null && newGame.topic_id !== undefined ? newGame.topic_id : null
    }
  } else {
    resetForm()
  }
}, { immediate: true })

const resetForm = () => {
  form.value = {
    name: '',
    date: '',
    location: '',
    start_time: '',
    opponent: '',
    chat_id: '-1002588984009',
    topic_id: 382
  }
}

const handleSubmit = () => {
  saving.value = true
  
  // Небольшая задержка для UX
  setTimeout(() => {
    emit('save', { ...form.value })
    saving.value = false
  }, 300)
}
</script>
