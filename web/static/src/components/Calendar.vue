<template>
  <div class="bg-white rounded shadow overflow-hidden">
    <!-- Заголовок с навигацией -->
    <div class="flex items-center justify-between p-4 border-b border-gray-200">
      <button
        @click="previousMonth"
        class="p-2 rounded hover:bg-gray-100 transition-colors"
      >
        ←
      </button>
      <h2 class="text-lg font-semibold text-gray-900">
        {{ monthName }} {{ currentYear }}
      </h2>
      <button
        @click="nextMonth"
        class="p-2 rounded hover:bg-gray-100 transition-colors"
      >
        →
      </button>
    </div>

    <!-- Сетка календаря -->
    <div class="grid grid-cols-7 border-b border-gray-200">
      <div
        v-for="day in dayNames"
        :key="day"
        class="py-2 text-center text-sm font-medium text-gray-500 border-r border-gray-100 last:border-r-0"
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
        class="min-h-[100px] bg-gray-50 border-r border-b border-gray-100"
      ></div>

      <!-- Дни месяца -->
      <div
        v-for="day in daysInMonth"
        :key="day"
        class="min-h-[100px] border-r border-b border-gray-100 last:border-r-0 p-2"
        :class="{ 'bg-gray-50': isWeekend(day) }"
      >
        <div class="text-sm font-medium text-gray-700 mb-1">
          {{ day }}
        </div>

        <!-- Тренировки в этот день -->
        <div class="space-y-1">
          <div
            v-for="training in getTrainingsForDay(day)"
            :key="training.key"
            @click="$emit('click-training', training)"
            class="text-xs p-1.5 rounded cursor-pointer transition-colors"
            :class="getTrainingClass(training)"
          >
            <div class="font-medium truncate">{{ training.time }}</div>
            <div class="truncate opacity-75">{{ training.registered_count }}/12</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  trainings: {
    type: Array,
    default: () => []
  }
})

defineEmits(['click-training'])

const currentDate = ref(new Date())

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
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1, 1)
  emitUpdate()
}

const nextMonth = () => {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1, 1)
  emitUpdate()
}

const emitUpdate = () => {
  // Можно добавить emit для уведомления родителя об изменении месяца
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
    return 'bg-teal-100 text-teal-800 hover:bg-teal-200'
  } else if (training.user_status === 'waitlist') {
    return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
  } else if (training.registered_count >= 12) {
    return 'bg-red-50 text-red-700 hover:bg-red-100'
  } else {
    return 'bg-gray-100 text-gray-700 hover:bg-gray-200'
  }
}
</script>
