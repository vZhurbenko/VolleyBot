<template>
  <div class="bg-white rounded shadow overflow-hidden border border-gray-200">
    <!-- Заголовок с навигацией -->
    <div class="flex items-center justify-between p-4 border-b border-gray-300 bg-gray-50">
      <button
        @click="previousMonth"
        class="p-2 rounded hover:bg-gray-200 transition-colors font-medium"
      >
        <ChevronLeft class="w-5 h-5" />
      </button>
      <h2 class="text-lg font-semibold text-gray-900">
        {{ monthName }} {{ currentYear }}
      </h2>
      <button
        @click="nextMonth"
        class="p-2 rounded hover:bg-gray-200 transition-colors font-medium"
      >
        <ChevronRight class="w-5 h-5" />
      </button>
    </div>

    <!-- Сетка календаря -->
    <div class="grid grid-cols-7 border-b border-gray-300">
      <div
        v-for="day in dayNames"
        :key="day"
        class="py-2 text-center text-sm font-semibold text-gray-700 border-r border-gray-200 last:border-r-0"
      >
        {{ day }}
      </div>
    </div>

    <!-- Дни месяца -->
    <div class="grid grid-cols-7 gap-px bg-gray-200">
      <!-- Пустые ячейки для дней предыдущего месяца -->
      <div
        v-for="n in firstDayOffset"
        :key="'empty-' + n"
        class="min-h-[100px] bg-gray-50"
      ></div>

      <!-- Дни месяца -->
      <div
        v-for="day in daysInMonth"
        :key="day"
        class="min-h-[100px] bg-white p-2 relative group"
        :class="{ 'bg-gray-50': isWeekend(day) }"
      >
        <div class="flex items-center justify-between mb-1 min-h-[20px]">
          <div class="text-sm font-semibold" :class="isWeekend(day) ? 'text-red-600' : 'text-gray-900'">
            {{ day }}
          </div>
          <!-- Кнопка добавления для админов -->
          <button
            v-if="isAdmin && !isPastDate(day)"
            @click="handleAddTraining(day)"
            class="opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center rounded bg-teal-100 text-teal-600 hover:bg-teal-200 transition-opacity"
            title="Добавить тренировку"
            :disabled="isPastDate(day)"
          >
            <Plus class="w-4 h-4" />
          </button>
        </div>

        <!-- Тренировки в этот день -->
        <div class="space-y-1 overflow-y-auto max-h-[120px]">
          <div
            v-for="training in getTrainingsForDay(day)"
            :key="training.key"
            @click="!isPastDate(day) && $emit('click-training', training)"
            class="text-xs p-1.5 rounded cursor-pointer transition-colors border"
            :class="getTrainingClass(training, day)"
          >
            <div class="font-medium truncate">{{ training.name || training.time }}</div>
            <div class="truncate opacity-75">{{ training.registered_count }}/12</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { Plus, ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  trainings: {
    type: Array,
    default: () => []
  },
  year: {
    type: Number,
    required: true
  },
  month: {
    type: Number,
    required: true
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click-training', 'update-month', 'add-training'])

// Следим за изменением пропсов year и month
watch([() => props.year, () => props.month], ([newYear, newMonth]) => {
  // Проверяем, что год корректный (не 1900-е годы)
  if (newYear && newYear > 2000 && newMonth >= 1 && newMonth <= 12) {
    // Props уже обновлены через v-model, watch нужен для валидации
  }
}, { immediate: true })

const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

// Используем props напрямую для реактивности
const monthName = computed(() => {
  const months = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ]
  return months[props.month - 1]
})

const currentYear = computed(() => props.year)

const daysInMonth = computed(() => {
  return new Date(props.year, props.month, 0).getDate()
})

const firstDayOffset = computed(() => {
  // Получаем день недели первого дня месяца (0 = воскресенье, 1 = понедельник, ...)
  let firstDay = new Date(props.year, props.month - 1, 1).getDay()
  // Преобразуем: 0 (вс) -> 6, 1 (пн) -> 0, 2 (вт) -> 1, ...
  firstDay = firstDay === 0 ? 6 : firstDay - 1
  return firstDay
})

const previousMonth = () => {
  // Вычисляем предыдущий месяц на основе props
  let prevYear = props.year
  let prevMonth = props.month - 1
  
  if (prevMonth < 1) {
    prevMonth = 12
    prevYear = props.year - 1
  }
  
  emit('update-month', { year: prevYear, month: prevMonth })
}

const nextMonth = () => {
  // Вычисляем следующий месяц на основе props
  let nextYear = props.year
  let nextMonth = props.month + 1
  
  if (nextMonth > 12) {
    nextMonth = 1
    nextYear = props.year + 1
  }
  
  emit('update-month', { year: nextYear, month: nextMonth })
}

const handleAddTraining = (day) => {
  const dateStr = `${props.year}-${String(props.month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  emit('add-training', dateStr)
}

const isPastDate = (day) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const date = new Date(props.year, props.month, day)
  return date < today
}

const isWeekend = (day) => {
  const date = new Date(props.year, props.month - 1, day)
  const dayOfWeek = date.getDay()
  return dayOfWeek === 0 || dayOfWeek === 6
}

const getTrainingsForDay = (day) => {
  const dateStr = `${props.year}-${String(props.month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  return props.trainings.filter(t => t.date === dateStr)
}

const getTrainingClass = (training, day) => {
  // Если тренировка прошла, делаем её серой и неактивной
  if (isPastDate(day)) {
    return 'bg-gray-200 text-gray-500 cursor-not-allowed border-gray-300 opacity-50'
  }
  if (training.user_status === 'registered') {
    return 'bg-teal-100 text-teal-800 hover:bg-teal-200 border-teal-200'
  } else if (training.user_status === 'waitlist') {
    return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200 border-yellow-200'
  } else if (training.registered_count >= 12) {
    return 'bg-red-100 text-red-800 hover:bg-red-200 border-red-200'
  } else {
    return 'bg-gray-100 text-gray-800 hover:bg-gray-200 border-gray-200'
  }
}
</script>
