<template>
  <div class="schedule-item">
    <div class="schedule-info">
      <h3 class="schedule-name">{{ schedule.name }}</h3>
      <p class="schedule-details">
        <span>{{ formatDay(schedule.training_day) }}</span>
        <span class="arrow">→</span>
        <span>{{ formatDay(schedule.poll_day) }}</span>
        <span class="dot">•</span>
        <span>{{ schedule.training_time }}</span>
      </p>
      <p class="schedule-chat">
        Chat: {{ schedule.chat_id }}
        <span v-if="schedule.message_thread_id" class="topic">
          (топик {{ schedule.message_thread_id }})
        </span>
      </p>
    </div>
    
    <div class="schedule-actions">
      <span :class="['tag', schedule.enabled ? 'tag-enabled' : 'tag-disabled']">
        {{ schedule.enabled ? 'Активно' : 'Отключено' }}
      </span>
      
      <button @click="$emit('edit', schedule)" class="btn-icon" title="Редактировать">
        ✎
      </button>
      <button @click="$emit('delete', schedule.id)" class="btn-icon btn-danger" title="Удалить">
        ✕
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  schedule: {
    type: Object,
    required: true
  }
})

defineEmits(['edit', 'delete'])

const days = {
  monday: 'Пн',
  tuesday: 'Вт',
  wednesday: 'Ср',
  thursday: 'Чт',
  friday: 'Пт',
  saturday: 'Сб',
  sunday: 'Вс'
}

const formatDay = (day) => days[day] || day
</script>

<style scoped>
.schedule-item {
  @apply flex items-center justify-between py-4 border-b border-gray-100 last:border-0;
}

.schedule-info {
  @apply flex-1;
}

.schedule-name {
  @apply font-semibold text-gray-900 mb-1;
}

.schedule-details {
  @apply text-sm text-gray-500 flex items-center gap-2 mb-1;
}

.arrow {
  @apply text-gray-400;
}

.dot {
  @apply text-gray-300;
}

.schedule-chat {
  @apply text-xs text-gray-400;
}

.topic {
  @apply text-gray-500;
}

.schedule-actions {
  @apply flex items-center gap-2;
}

.tag {
  @apply px-3 py-1 rounded-full text-xs font-medium;
}

.tag-enabled {
  @apply bg-green-100 text-green-700;
}

.tag-disabled {
  @apply bg-red-100 text-red-700;
}

.btn-icon {
  @apply w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors;
}

.btn-danger {
  @apply text-red-500 hover:bg-red-50;
}
</style>
