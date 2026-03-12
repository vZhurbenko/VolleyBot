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
          <h3 class="text-lg font-semibold text-gray-900">{{ game?.name || 'Игра' }}</h3>
          <p class="text-sm text-gray-500">
            {{ formatDate(game?.date)
            }}<span v-if="game?.start_time"> • {{ game.start_time }}</span>
          </p>
          <p v-if="game?.opponent" class="text-sm text-gray-600 mt-1">vs {{ game.opponent }}</p>
          <p v-if="game?.location" class="text-sm text-gray-600">{{ game.location }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="shareGame"
            class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100"
            title="Поделиться"
          >
            <Link class="w-4 h-4 text-gray-600" />
          </button>
          <button
            @click="handleClose"
            class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100"
          >
            <X class="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      <!-- Контент -->
      <div class="p-6">
        <!-- Результат если есть -->
        <div v-if="game?.result" class="mb-4 p-3 rounded-lg" :class="getResultClass(game.result)">
          <p class="text-sm font-medium flex items-center gap-2">
            <Trophy class="w-4 h-4" />
            {{ getResultText(game.result) }}
            <span v-if="game?.score" class="font-bold">{{ game.score }}</span>
          </p>
        </div>

        <!-- Кнопка действия -->
        <button
          @click="handleSignup"
          class="w-full h-11 px-6 rounded font-medium transition-colors mb-4"
          :class="actionButtonClass"
        >
          {{ actionButtonText }}
        </button>

        <!-- Список записавшихся -->
        <div v-if="game?.signups && game.signups.length > 0">
          <h4 class="text-sm font-semibold text-gray-700 mb-2">
            Записались ({{ game.signups.length }})
          </h4>
          <div class="space-y-2">
            <div
              v-for="signup in game.signups"
              :key="signup.id"
              class="flex items-center gap-3 p-2 bg-gray-50 rounded"
            >
              <img
                v-if="signup.photo_url"
                :src="signup.photo_url"
                alt=""
                class="w-8 h-8 rounded-full"
              />
              <div
                v-else
                class="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold text-xs"
              >
                {{ getInitials(signup) }}
              </div>
              <span class="text-sm text-gray-700 flex-1">
                {{ signup.first_name }} {{ signup.last_name || '' }}
                <span v-if="signup.username" class="text-gray-400">@{{ signup.username }}</span>
              </span>
            </div>
          </div>
        </div>
        <div v-else class="text-gray-500 text-sm text-center py-4">Пока никто не записался</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { X, Trophy, Link } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

const props = defineProps({
  game: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['close', 'signup', 'update-game'])

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()

const isSignedUp = computed(() => {
  return props.game?.signups?.some((s) => s.user_telegram_id === authStore.user?.telegram_id)
})

const actionButtonClass = computed(() => {
  if (isSignedUp.value) {
    return 'text-red-600 hover:text-red-700 bg-transparent'
  }
  return 'bg-teal-600 text-white hover:bg-teal-700'
})

const actionButtonText = computed(() => {
  return isSignedUp.value ? 'Выписаться' : 'Записаться'
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    weekday: 'short',
  })
}

const getResultClass = (result) => {
  switch (result) {
    case 'win':
      return 'bg-green-100 text-green-800 border border-green-200'
    case 'loss':
      return 'bg-red-100 text-red-800 border border-red-200'
    case 'draw':
      return 'bg-yellow-100 text-yellow-800 border border-yellow-200'
    default:
      return 'bg-gray-100 text-gray-800 border border-gray-200'
  }
}

const getResultText = (result) => {
  switch (result) {
    case 'win':
      return 'Победа'
    case 'loss':
      return 'Поражение'
    case 'draw':
      return 'Ничья'
    default:
      return result
  }
}

const getInitials = (user) => {
  const first = user.first_name?.charAt(0) || ''
  const last = user.last_name?.charAt(0) || ''
  return (first + last).toUpperCase()
}

const handleSignup = () => {
  emit('update-game')
}

const shareGame = () => {
  // Генерируем универсальную ссылку /t/{uuid}
  // Бэкенд сам определит куда редиректить: гостя на страницу гостя, пользователя в модалку
  if (props.game?.uuid) {
    const url = `${window.location.origin}/t/${props.game.uuid}`
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
    const url = `${window.location.origin}/dashboard/calendar?game_id=${props.game?.id}`
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

const handleClose = () => {
  console.log('[GameModal] handleClose вызван')
  
  // Сначала закрываем модалку
  emit('close')
  
  // Затем очищаем параметр game_id из URL
  const newQuery = { ...route.query }
  delete newQuery.game_id
  console.log('[GameModal] Новый query:', newQuery)
  
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
