<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click="$emit('close')">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md" @click.stop>
      <!-- Заголовок -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white rounded-t-lg">
        <h3 class="text-lg font-semibold text-gray-900">
          Результат игры
        </h3>
        <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Содержимое -->
      <div class="p-6 space-y-4">
        <form id="game-result-form" @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Информация об игре -->
          <div v-if="game" class="p-4 bg-gray-50 rounded-lg">
            <h3 class="font-semibold text-gray-900">{{ game.name }}</h3>
            <div v-if="game.opponent" class="text-gray-600 mt-1">vs {{ game.opponent }}</div>
            <div class="text-sm text-gray-500 mt-2">
              {{ formatDate(game.date) }}
              <span v-if="game.start_time">{{ game.start_time }}</span>
            </div>
            <div v-if="game.location" class="text-sm text-gray-500">{{ game.location }}</div>
          </div>

          <div class="space-y-4">
          <!-- Исход игры -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Исход игры *
            </label>
            <div class="grid grid-cols-3 gap-3">
              <label
                class="relative flex flex-col items-center p-4 border-2 rounded-lg cursor-pointer transition-colors"
                :class="form.result === 'win' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300'"
              >
                <input
                  v-model="form.result"
                  type="radio"
                  value="win"
                  class="sr-only"
                />
                <Trophy class="w-6 h-6 text-green-600 mb-2" />
                <span class="text-sm font-medium text-gray-900">Победа</span>
              </label>

              <label
                class="relative flex flex-col items-center p-4 border-2 rounded-lg cursor-pointer transition-colors"
                :class="form.result === 'draw' ? 'border-yellow-500 bg-yellow-50' : 'border-gray-200 hover:border-gray-300'"
              >
                <input
                  v-model="form.result"
                  type="radio"
                  value="draw"
                  class="sr-only"
                />
                <Minus class="w-6 h-6 text-yellow-600 mb-2" />
                <span class="text-sm font-medium text-gray-900">Ничья</span>
              </label>

              <label
                class="relative flex flex-col items-center p-4 border-2 rounded-lg cursor-pointer transition-colors"
                :class="form.result === 'loss' ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'"
              >
                <input
                  v-model="form.result"
                  type="radio"
                  value="loss"
                  class="sr-only"
                />
                <X class="w-6 h-6 text-red-600 mb-2" />
                <span class="text-sm font-medium text-gray-900">Поражение</span>
              </label>
            </div>
          </div>

          <!-- Счёт -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Счёт *
            </label>
            <input
              v-model="form.score"
              type="text"
              required
              placeholder="3:1"
              pattern="\d+:\d+"
              title="Формат счёта: 3:1"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
            <p class="text-xs text-gray-500 mt-1">Формат: 3:1, 2:3 и т.д.</p>
          </div>
          </div>
        </form>
      </div>

      <!-- Кнопки -->
      <div class="px-6 py-4 border-t border-gray-100 flex justify-between gap-2">
        <button
          v-if="game?.result"
          type="button"
          @click="clearResult"
          class="h-11 px-6 rounded font-medium transition-colors text-red-600 hover:text-red-700 bg-transparent"
        >
          Сбросить
        </button>
        <div class="flex gap-2 ml-auto">
          <button
            type="submit"
            :disabled="saving || !form.result"
            form="game-result-form"
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
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { X, Trophy, Minus } from 'lucide-vue-next'

const props = defineProps({
  game: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

const form = ref({
  result: '',
  score: ''
})

const saving = ref(false)

watch(() => props.game, (newGame) => {
  if (newGame) {
    form.value = {
      result: newGame.result || '',
      score: newGame.score || ''
    }
  } else {
    resetForm()
  }
}, { immediate: true })

const resetForm = () => {
  form.value = {
    result: '',
    score: ''
  }
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    weekday: 'short'
  })
}

const handleSubmit = () => {
  if (!form.value.result || !form.value.score) {
    return
  }

  saving.value = true

  setTimeout(() => {
    emit('save', { ...form.value })
    saving.value = false
  }, 300)
}

const clearResult = () => {
  emit('save', { result: '', score: '' })
}
</script>
