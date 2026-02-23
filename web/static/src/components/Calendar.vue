<template>
  <div class="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
    <!-- Заголовок с навигацией -->
    <div class="flex items-center justify-between p-4 bg-gray-50 border-b border-gray-300">
      <button
        @click="previousMonth"
        class="p-2 rounded-lg hover:bg-gray-200 transition-colors font-bold text-gray-700"
      >
        ←
      </button>
      <h2 class="text-lg font-bold text-gray-900">
        {{ monthName }} {{ currentYear }}
      </h2>
      <button
        @click="nextMonth"
        class="p-2 rounded-lg hover:bg-gray-200 transition-colors font-bold text-gray-700"
      >
        →
      </button>
    </div>

    <!-- Сетка календаря -->
    <div class="grid grid-cols-7 border-b border-gray-300 bg-gray-100">
      <div
        v-for="day in dayNames"
        :key="day"
        class="py-3 text-center text-sm font-bold text-gray-700 border-r border-gray-300 last:border-r-0"
      >
        {{ day }}
      </div>
    </div>

    <!-- Дни месяца -->
    <div class="grid grid-cols-7">
      <!-- Пустые ячейки для дней предыдущего месяца -->
      <div
        v-for="n in firstDayOffset"
        :key="'empty-' + n"
        class="min-h-[120px] bg-gray-50 border-r border-b border-gray-300"
      ></div>

      <!-- Дни месяца -->
      <div
        v-for="day in daysInMonth"
        :key="day"
        class="min-h-[120px] border-r border-b border-gray-300 last:border-r-0 p-2 relative group"
        :class="{ 'bg-red-50': isWeekend(day), 'bg-white': !isWeekend(day) }"
      >
        <div class="flex items-center justify-between mb-2 min-h-[20px]">
          <div class="text-base font-bold text-gray-900" :class="{ 'text-red-700': isWeekend(day) }">
            {{ day }}
          </div>
          <!-- Кнопка добавления для админов -->
          <button
            v-if="isAdmin"
            @click="handleAddTraining(day)"
            class="opacity-0 group-hover:opacity-100 w-7 h-7 flex items-center justify-center rounded-lg bg-teal-600 text-white hover:bg-teal-700 transition-opacity font-bold text-lg shadow"
            title="Добавить тренировку"
          >
            +
          </button>
        </div>

        <!-- Тренировки в этот день -->
        <div class="space-y-1.5 overflow-y-auto max-h-[100px]">
          <div
            v-for="training in getTrainingsForDay(day)"
            :key="training.key"
            @click="$emit('click-training', training)"
            class="text-xs p-2 rounded-md cursor-pointer transition-all hover:scale-105 shadow-sm"
            :class="getTrainingClass(training)"
          >
            <div class="font-bold">{{ training.time }}</div>
            <div class="opacity-80 font-medium">{{ training.registered_count }}/12</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  trainings: {
    type: Array,
    default: () => []
  },
  year: {
    type: Number,
    default: () => new Date().getFullYear()
  },
  month: {
    type: Number,
    default: () => new Date().getMonth() + 1
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click-training', 'update:year', 'update:month', 'add-training'])

const currentDate = ref(new Date(props.year, props.month - 1, 1))

// Следим за изменением пропсов
watch(() => [props.year, props.month], ([newYear, newMonth]) => {
  currentDate.value = new Date(newYear, newMonth - 1, 1)
})

const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const monthName = computed(() => {
  const months = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ]
  return months[currentDate.value.getMonth()]
})

const currentYear = computed(() => currentDate.value.getFullYear())

const daysInMonth = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  return new Date(year, month + 1, 0).getDate()
})

const firstDayOffset = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  // Получаем день недели первого дня месяца (0 = воскресенье, 1 = понедельник, ...)
  let firstDay = new Date(year, month, 1).getDay()
  // Преобразуем: 0 (вс) -> 6, 1 (пн) -> 0, 2 (вт) -> 1, ...
  firstDay = firstDay === 0 ? 6 : firstDay - 1
  return firstDay
})

const previousMonth = () => {
  const newDate = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1, 1)
  currentDate.value = newDate
  emit('update:year', newDate.getFullYear())
  emit('update:month', newDate.getMonth() + 1)
}

const nextMonth = () => {
  const newDate = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1, 1)
  currentDate.value = newDate
  emit('update:year', newDate.getFullYear())
  emit('update:month', newDate.getMonth() + 1)
}

const handleAddTraining = (day) => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth() + 1
  const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  emit('add-training', dateStr)
}

const isWeekend = (day) => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  const date = new Date(year, month, day)
  const dayOfWeek = date.getDay()
  return dayOfWeek === 0 || dayOfWeek === 6
}

const getTrainingsForDay = (day) => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth() + 1
  const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  
  return props.trainings.filter(t => t.date === dateStr)
}

const getTrainingClass = (training) => {
  if (training.user_status === 'registered') {
    return 'bg-teal-500 text-white hover:bg-teal-600 border border-teal-600'
  } else if (training.user_status === 'waitlist') {
    return 'bg-yellow-500 text-white hover:bg-yellow-600 border border-yellow-600'
  } else if (training.registered_count >= 12) {
    return 'bg-red-500 text-white hover:bg-red-600 border border-red-600'
  } else {
    return 'bg-gray-200 text-gray-800 hover:bg-gray-300 border border-gray-300'
  }
}
</script>
