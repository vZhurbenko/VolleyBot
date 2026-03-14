<template>
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    @click="handleClose"
  >
    <div
      class="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-auto"
      @click.stop
    >
      <!-- Заголовок -->
      <div
        class="px-6 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white"
      >
        <div>
          <h3 class="text-lg font-semibold text-gray-900">{{ training.name || 'Тренировка' }}</h3>
          <p class="text-sm text-gray-500">{{ formatDate(training.date) }} • {{ training.time }}</p>
          <p v-if="training.location" class="text-sm text-gray-600 mt-1">{{ training.location }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="shareTraining"
            class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100"
            title="Поделиться"
          >
            <Link class="w-4 h-4 text-gray-600" />
          </button>
          <button
            @click="handleClose"
            class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100"
            title="Закрыть"
          >
            <X class="w-4 h-4 text-gray-600" />
          </button>
        </div>
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
              <img v-if="reg.photo_url" :src="reg.photo_url" alt="" class="w-8 h-8 rounded-full" />
              <div
                v-else
                class="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold text-xs"
              >
                {{ getInitials(reg) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-sm text-gray-700 truncate">
                    {{ reg.first_name }} {{ reg.last_name || '' }}
                    <span v-if="reg.username" class="text-gray-400">@{{ reg.username }}</span>
                  </span>
                  <!-- Значок роли -->
                  <Shield
                    v-if="reg.is_admin"
                    class="w-4 h-4 text-purple-600 flex-shrink-0"
                    title="Администратор"
                  />
                  <BadgeCheck
                    v-else-if="!reg.is_guest"
                    class="w-4 h-4 text-teal-600 flex-shrink-0"
                    title="Участник"
                  />
                  <User
                    v-else
                    class="w-4 h-4 text-blue-600 flex-shrink-0"
                    title="Гость"
                  />
                </div>
              </div>
              <!-- Кнопка удаления для админа -->
              <button
                v-if="isAdmin"
                @click="removeUser(reg)"
                class="w-8 h-8 flex items-center justify-center rounded hover:bg-red-50 text-red-500 transition-colors flex-shrink-0"
                title="Удалить участника"
              >
                <X class="w-4 h-4" />
              </button>
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
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-700 truncate">
                      {{ reg.first_name }} {{ reg.last_name || '' }}
                      <span v-if="reg.username" class="text-gray-400">@{{ reg.username }}</span>
                    </span>
                    <!-- Значок роли -->
                    <Shield
                      v-if="reg.is_admin"
                      class="w-4 h-4 text-purple-600 flex-shrink-0"
                      title="Администратор"
                    />
                    <BadgeCheck
                      v-else-if="!reg.is_guest"
                      class="w-4 h-4 text-teal-600 flex-shrink-0"
                      title="Участник"
                    />
                    <User
                      v-else
                      class="w-4 h-4 text-blue-600 flex-shrink-0"
                      title="Гость"
                    />
                  </div>
                </div>
                <!-- Кнопка удаления для админа -->
                <button
                  v-if="isAdmin"
                  @click="removeUser(reg)"
                  class="w-8 h-8 flex items-center justify-center rounded hover:bg-red-50 text-red-500 transition-colors flex-shrink-0"
                  title="Удалить участника"
                >
                  <X class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-gray-500 text-center py-8">Пока никто не записался</div>

        <!-- Кнопка удаления для админа -->
        <div v-if="isAdmin && (training.is_one_time || training.event_type === 'one_time_training' || training.event_type === 'scheduled_training')" class="mt-4 pt-4 border-t border-gray-200">
          <button
            @click="$emit('remove-training')"
            class="w-full h-11 px-6 rounded font-medium transition-colors text-red-600 hover:text-red-700 bg-transparent"
          >
            Удалить тренировку
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { useConfirmStore } from '@/stores/confirm'
import { Link, X, Shield, User, BadgeCheck } from 'lucide-vue-next'

const props = defineProps({
  training: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['close', 'register', 'unregister', 'remove-training', 'remove-user'])

const router = useRouter()
const route = useRoute()

const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const confirmStore = useConfirmStore()

const isAdmin = computed(() => authStore.isAdmin)

const registeredUsers = computed(() => {
  return (props.training.registrations || []).filter((r) => r.status === 'registered')
})

const waitlistUsers = computed(() => {
  return (props.training.registrations || []).filter((r) => r.status === 'waitlist')
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
  if (props.training.user_status === 'registered') {
    return 'text-red-600 hover:text-red-700 bg-transparent'
  } else if (props.training.user_status === 'waitlist') {
    return 'text-red-600 hover:text-red-700 bg-transparent'
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

const shareTraining = () => {
  // Генерируем универсальную ссылку /t/{uuid}
  // Бэкенд сам определит куда редиректить: гостя на страницу гостя, пользователя в модалку
  if (props.training.uuid) {
    const url = `${window.location.origin}/t/${props.training.uuid}`
    navigator.clipboard
      .writeText(url)
      .then(() => {
        notificationsStore.success('Ссылка скопирована в буфер обмена')
      })
      .catch(() => {
        notificationsStore.error('Не удалось скопировать ссылку')
      })
  } else {
    // Фоллбэк на старую ссылку если uuid нет
    const url = `${window.location.origin}/dashboard/calendar?date=${props.training.date}&chat_id=${props.training.chat_id}&time=${encodeURIComponent(props.training.time)}`
    navigator.clipboard
      .writeText(url)
      .then(() => {
        notificationsStore.success('Ссылка скопирована в буфер обмена')
      })
      .catch(() => {
        notificationsStore.error('Не удалось скопировать ссылку')
      })
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const [year, month, day] = dateStr.split('-')
  return `${day}.${month}.${year}`
}

const getInitials = (reg) => {
  const first = reg.first_name?.[0] || ''
  const last = reg.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}

const removeUser = async (reg) => {
  const name = reg.first_name + (reg.last_name ? ' ' + reg.last_name : '')
  const confirmed = await confirmStore.danger(`Удалить ${name} из тренировки?`)
  if (confirmed) {
    emit('remove-user', reg)
  }
}

const handleClose = () => {
  console.log('[TrainingModal] handleClose вызван')
  
  // Сначала закрываем модалку
  emit('close')
  
  // Затем очищаем параметр training из URL
  const newQuery = { ...route.query }
  delete newQuery.training
  console.log('[TrainingModal] Новый query:', newQuery)
  
  // Используем router.replace для обновления URL
  router.replace({ query: newQuery })
}

// Обработчик нажатия клавиш
const handleKeydown = (e) => {
  if (e.key === 'Escape') {
    handleClose()
  }
}

// Подписка на события клавиатуры при монтировании
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

// Очистка при размонтировании
onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>
