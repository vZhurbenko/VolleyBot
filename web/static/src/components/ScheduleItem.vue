<template>
  <div
    class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-4 border-b border-gray-100 last:border-0"
  >
    <div class="flex-1 min-w-0">
      <h3 class="font-semibold text-gray-900 mb-1 truncate">{{ schedule.name }}</h3>
      <p class="text-sm text-gray-500 mb-1 whitespace-nowrap">
        <span class="font-medium text-gray-700">Тренировка:</span>
        {{ formatDay(schedule.training_day) }}, {{ schedule.start_time }} - {{ schedule.end_time }},
        {{ schedule.location }}
        <span class="mx-1 text-gray-300">|</span>
        <span class="font-medium text-gray-700">Опрос:</span> {{ formatDay(pollDay) }}
      </p>
      <p class="text-xs text-gray-400 truncate">
        Chat: {{ schedule.chat_id }}
        <span v-if="schedule.message_thread_id" class="text-gray-500">
          (топик {{ schedule.message_thread_id }})
        </span>
      </p>
    </div>

    <div class="flex items-center gap-2 flex-shrink-0">
      <span
        :class="[
          'px-3 py-1 rounded text-xs font-medium whitespace-nowrap',
          schedule.enabled ? 'bg-teal-100 text-teal-700' : 'bg-red-100 text-red-700',
        ]"
      >
        {{ schedule.enabled ? 'Активно' : 'Отключено' }}
      </span>

      <button
        @click="$emit('edit', schedule)"
        class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100 transition-colors flex-shrink-0"
        title="Редактировать"
      >
        <Edit2 class="w-4 h-4 text-gray-600" />
      </button>
      <button
        @click="$emit('delete', schedule.id)"
        class="w-8 h-8 flex items-center justify-center rounded hover:bg-red-50 text-red-500 transition-colors flex-shrink-0"
        title="Удалить"
      >
        <X class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { X, Edit2 } from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps({
  schedule: {
    type: Object,
    required: true,
  },
})

defineEmits(['edit', 'delete'])

const days = {
  monday: 'Пн',
  tuesday: 'Вт',
  wednesday: 'Ср',
  thursday: 'Чт',
  friday: 'Пт',
  saturday: 'Сб',
  sunday: 'Вс',
}

const dayOrder = {
  monday: 0,
  tuesday: 1,
  wednesday: 2,
  thursday: 3,
  friday: 4,
  saturday: 5,
  sunday: 6,
}

const formatDay = (day) => days[day] || day

// Вычисляем день опроса (за 3 дня до тренировки)
const pollDay = computed(() => {
  const trainingDay = props.schedule?.training_day
  if (!trainingDay) return ''

  const trainingDayIndex = dayOrder[trainingDay]
  // Опрос за 3 дня до тренировки
  const pollDayIndex = (trainingDayIndex - 3 + 7) % 7
  return Object.keys(dayOrder).find((key) => dayOrder[key] === pollDayIndex) || trainingDay
})
</script>
