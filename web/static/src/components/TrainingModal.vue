<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click="$emit('close')">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-auto" @click.stop>
      <!-- Заголовок -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">Тренировка</h3>
          <p class="text-sm text-gray-500">{{ training.date }} • {{ training.time }}</p>
        </div>
        <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100">
          ✕
        </button>
      </div>

      <!-- Контент -->
      <div class="p-6">
        <!-- Статус записи пользователя -->
        <div v-if="training.user_status" class="mb-4 p-3 rounded-lg" :class="userStatusClass">
          <p class="text-sm font-medium" :class="userStatusTextClass">
            {{ userStatusText }}
          </p>
        </div>

        <!-- Кнопка действия -->
        <button
          @click="handleAction"
          class="w-full h-11 px-6 rounded font-medium transition-colors mb-4"
          :class="actionButtonClass"
        >
          {{ actionButtonText }}
        </button>

        <!-- Список записавшихся -->
        <div v-if="training.registrations && training.registrations.length > 0">
          <h4 class="text-sm font-semibold text-gray-700 mb-2">
            Записались ({{ training.registered_count }}/12)
          </h4>
          
          <!-- Основные участники -->
          <div class="space-y-2 mb-4">
            <div
              v-for="reg in registeredUsers"
              :key="reg.user_telegram_id"
              class="flex items-center gap-3 p-2 bg-gray-50 rounded"
            >
              <img
                v-if="reg.photo_url"
                :src="reg.photo_url"
                alt=""
                class="w-8 h-8 rounded-full"
              />
              <div
                v-else
                class="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold text-xs"
              >
                {{ getInitials(reg) }}
              </div>
              <span class="text-sm text-gray-700">
                {{ reg.first_name }} {{ reg.last_name || '' }}
                <span v-if="reg.username" class="text-gray-400">@{{ reg.username }}</span>
              </span>
            </div>
          </div>

          <!-- Резерв -->
          <div v-if="waitlistUsers.length > 0">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">
              Резерв ({{ training.waitlist_count }})
            </h4>
            <div class="space-y-2">
              <div
                v-for="reg in waitlistUsers"
                :key="reg.user_telegram_id"
                class="flex items-center gap-3 p-2 bg-yellow-50 rounded"
              >
                <img
                  v-if="reg.photo_url"
                  :src="reg.photo_url"
                  alt=""
                  class="w-8 h-8 rounded-full"
                />
                <div
                  v-else
                  class="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold text-xs"
                >
                  {{ getInitials(reg) }}
                </div>
                <span class="text-sm text-gray-700">
                  {{ reg.first_name }} {{ reg.last_name || '' }}
                  <span v-if="reg.username" class="text-gray-400">@{{ reg.username }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-gray-500 text-center py-8">
          Пока никто не записался
        </div>

        <!-- Кнопка удаления для админа -->
        <div v-if="isAdmin && training.is_one_time" class="mt-4 pt-4 border-t border-gray-200">
          <button
            @click="$emit('remove-training')"
            class="w-full h-11 px-6 rounded font-medium transition-colors bg-red-500 text-white hover:bg-red-600"
          >
            Удалить тренировку
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  training: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'register', 'unregister', 'remove-training'])

const authStore = useAuthStore()

const isAdmin = computed(() => authStore.isAdmin)

const registeredUsers = computed(() => {
  return (props.training.registrations || []).filter(r => r.status === 'registered')
})

const waitlistUsers = computed(() => {
  return (props.training.registrations || []).filter(r => r.status === 'waitlist')
})

const userStatusClass = computed(() => {
  if (props.training.user_status === 'registered') {
    return 'bg-teal-50 border border-teal-200'
  } else if (props.training.user_status === 'waitlist') {
    return 'bg-yellow-50 border border-yellow-200'
  }
  return ''
})

const userStatusTextClass = computed(() => {
  if (props.training.user_status === 'registered') {
    return 'text-teal-800'
  } else if (props.training.user_status === 'waitlist') {
    return 'text-yellow-800'
  }
  return ''
})

const userStatusText = computed(() => {
  if (props.training.user_status === 'registered') {
    return '✓ Вы записаны на тренировку'
  } else if (props.training.user_status === 'waitlist') {
    return '⏳ Вы в резерве'
  }
  return ''
})

const actionButtonText = computed(() => {
  if (props.training.user_status === 'registered') {
    return 'Выписаться'
  } else if (props.training.user_status === 'waitlist') {
    return 'Отменить запись'
  } else if (props.training.registered_count >= 12) {
    return 'Записаться в резерв'
  } else {
    return 'Записаться'
  }
})

const actionButtonClass = computed(() => {
  if (props.training.user_status) {
    return 'bg-red-500 text-white hover:bg-red-600'
  } else if (props.training.registered_count >= 12) {
    return 'bg-yellow-500 text-white hover:bg-yellow-600'
  } else {
    return 'bg-teal-600 text-white hover:bg-teal-700'
  }
})

const handleAction = () => {
  if (props.training.user_status) {
    emit('unregister')
  } else {
    emit('register')
  }
}

const getInitials = (reg) => {
  const first = reg.first_name?.[0] || ''
  const last = reg.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}
</script>
