<template>
  <div class="flex flex-col gap-4 lg:gap-6">
    <!-- Заголовок -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <BarChart3 class="w-8 h-8 text-teal-600" />
        <h1 class="text-2xl font-bold text-gray-900">Статистика тренировок</h1>
      </div>
      
      <!-- Выбор периода -->
      <div class="flex gap-2">
        <button
          v-for="p in periods"
          :key="p.value"
          @click="selectedPeriod = p.value; loadAllStats()"
          :class="[
            'px-3 py-1.5 rounded text-sm font-medium transition-colors',
            selectedPeriod === p.value
              ? 'bg-teal-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          {{ p.label }}
        </button>
      </div>
    </div>

    <!-- Вкладки -->
    <div class="border-b border-gray-200">
      <nav class="-mb-px flex gap-4">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'pb-2 px-1 border-b-2 font-medium text-sm transition-colors',
            activeTab === tab.id
              ? 'border-teal-500 text-teal-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          ]"
        >
          {{ tab.label }}
        </button>
      </nav>
    </div>

    <!-- Общая статистика по тренировкам -->
    <div v-if="activeTab === 'overview'" class="flex flex-col gap-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <p class="text-sm text-gray-500 mb-2">Тренировок</p>
          <p class="text-3xl font-bold text-gray-900">{{ overviewStats.total_trainings || 0 }}</p>
        </div>
        
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <p class="text-sm text-gray-500 mb-2">Всего записей</p>
          <p class="text-3xl font-bold text-gray-900">{{ overviewStats.total_signups || 0 }}</p>
        </div>
        
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <p class="text-sm text-gray-500 mb-2">Уникальных пользователей</p>
          <p class="text-3xl font-bold text-gray-900">{{ overviewStats.unique_users || 0 }}</p>
        </div>
        
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <p class="text-sm text-gray-500 mb-2">В среднем на тренировку</p>
          <p class="text-3xl font-bold text-gray-900">{{ overviewStats.avg_per_training || 0 }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <h3 class="font-semibold text-gray-900 mb-4">Распределение по типам</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <BadgeCheck class="w-5 h-5 text-teal-600" />
                <span class="text-gray-700">Участники</span>
              </div>
              <span class="font-semibold text-gray-900">{{ overviewStats.users_count || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <User class="w-5 h-5 text-blue-600" />
                <span class="text-gray-700">Гости</span>
              </div>
              <span class="font-semibold text-gray-900">{{ overviewStats.guests_count || 0 }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded shadow p-4 lg:p-6">
          <h3 class="font-semibold text-gray-900 mb-4">Период</h3>
          <p class="text-gray-700">
            {{ overviewStats.date_range?.from || '—' }} — {{ overviewStats.date_range?.to || '—' }}
          </p>
        </div>
      </div>
    </div>

    <!-- Общая статистика по играм -->
    <div v-if="activeTab === 'games'" class="flex flex-col gap-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <p class="text-sm text-gray-500 mb-2">Игр</p>
          <p class="text-3xl font-bold text-gray-900">{{ gamesStats.total_games || 0 }}</p>
        </div>
        
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <p class="text-sm text-gray-500 mb-2">Всего записей</p>
          <p class="text-3xl font-bold text-gray-900">{{ gamesStats.total_signups || 0 }}</p>
        </div>
        
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <p class="text-sm text-gray-500 mb-2">Уникальных пользователей</p>
          <p class="text-3xl font-bold text-gray-900">{{ gamesStats.unique_users || 0 }}</p>
        </div>
        
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <p class="text-sm text-gray-500 mb-2">В среднем на игру</p>
          <p class="text-3xl font-bold text-gray-900">{{ gamesStats.avg_per_game || 0 }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <h3 class="font-semibold text-gray-900 mb-4">Распределение по типам</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <BadgeCheck class="w-5 h-5 text-teal-600" />
                <span class="text-gray-700">Участники</span>
              </div>
              <span class="font-semibold text-gray-900">{{ gamesStats.users_count || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <User class="w-5 h-5 text-blue-600" />
                <span class="text-gray-700">Гости</span>
              </div>
              <span class="font-semibold text-gray-900">{{ gamesStats.guests_count || 0 }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded shadow p-4 lg:p-6">
          <h3 class="font-semibold text-gray-900 mb-4">Период</h3>
          <p class="text-gray-700">
            {{ gamesStats.date_range?.from || '—' }} — {{ gamesStats.date_range?.to || '—' }}
          </p>
        </div>
      </div>
    </div>

    <!-- Топ пользователей -->
    <div v-if="activeTab === 'top_users'" class="bg-white rounded shadow p-4 lg:p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-900">Статистика пользователей</h3>
        <p class="text-sm text-gray-500">
          Всего мероприятий: <span class="font-semibold">{{ totalEvents }}</span>
          <span v-if="trainingsCount || gamesCount" class="text-gray-400">
            ({{ trainingsCount }} тренир., {{ gamesCount }} игр)
          </span>
        </p>
      </div>
      
      <div v-if="topUsers.length > 0" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Пользователь</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Тренировки</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Игры</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Всего</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">% посещаемости</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr
              v-for="(user, index) in topUsers"
              :key="user.telegram_id"
              class="hover:bg-gray-50 cursor-pointer"
              @click="showUserStats(user.telegram_id)"
            >
              <td class="px-4 py-3 text-sm text-gray-900">{{ index + 1 }}</td>
              <td class="px-4 py-3 text-sm">
                <div class="flex items-center gap-2">
                  <User v-if="user.is_guest" class="w-4 h-4 text-blue-600" />
                  <span class="font-medium text-gray-900">
                    {{ user.username ? '@' + user.username : user.first_name + ' ' + (user.last_name || '') }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-3 text-sm text-center">{{ user.trainings_count || 0 }}</td>
              <td class="px-4 py-3 text-sm text-center">{{ user.games_count || 0 }}</td>
              <td class="px-4 py-3 text-sm text-center font-semibold text-gray-900">{{ user.total_count || 0 }}</td>
              <td class="px-4 py-3 text-sm text-center">
                <span
                  :class="[
                    'px-2 py-1 rounded text-xs font-semibold',
                    user.attendance_percent >= 75 ? 'bg-green-100 text-green-700' :
                    user.attendance_percent >= 50 ? 'bg-yellow-100 text-yellow-700' :
                    user.attendance_percent > 0 ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-500'
                  ]"
                >
                  {{ user.attendance_percent || 0 }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="text-center py-8 text-gray-500">
        Нет данных за выбранный период
      </div>
    </div>

    <!-- Статистика по дате -->
    <div v-if="activeTab === 'by_date'" class="flex flex-col gap-4">
      <!-- Выбор даты -->
      <div class="bg-white rounded shadow p-4 lg:p-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">Выберите дату</label>
        <input
          v-model="selectedDate"
          type="date"
          class="w-full max-w-xs px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
          @change="loadTrainingDetails"
        />
      </div>

      <!-- Детали тренировки -->
      <div v-if="trainingDetails.training_info" class="bg-white rounded shadow p-4 lg:p-6">
        <h3 class="font-semibold text-gray-900 mb-4">
          {{ trainingDetails.training_info.name || 'Тренировка' }}
        </h3>
        
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div>
            <p class="text-sm text-gray-500">Время</p>
            <p class="font-medium text-gray-900">
              {{ trainingDetails.training_info.start_time }} - {{ trainingDetails.training_info.end_time }}
            </p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Место</p>
            <p class="font-medium text-gray-900">{{ trainingDetails.training_info.location || '—' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Участников</p>
            <p class="font-medium text-gray-900">{{ trainingDetails.stats?.total || 0 }}</p>
          </div>
        </div>

        <div v-if="trainingDetails.participants && trainingDetails.participants.length > 0">
          <h4 class="font-medium text-gray-900 mb-3">Участники ({{ trainingDetails.participants.length }})</h4>
          <div class="space-y-2 max-h-96 overflow-y-auto">
            <div
              v-for="(p, index) in trainingDetails.participants"
              :key="index"
              class="flex items-center justify-between p-2 bg-gray-50 rounded"
            >
              <div class="flex items-center gap-2">
                <User v-if="p.is_guest" class="w-4 h-4 text-blue-600" />
                <span class="text-gray-900">
                  {{ p.username ? '@' + p.username : p.first_name + ' ' + (p.last_name || '') }}
                </span>
              </div>
              <span
                :class="[
                  'px-2 py-0.5 rounded text-xs font-medium',
                  p.status === 'registered' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                ]"
              >
                {{ p.status === 'registered' ? 'Записан' : 'Лист ожидания' }}
              </span>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-8 text-gray-500">
          Нет участников на эту дату
        </div>
      </div>

      <div v-else-if="selectedDate" class="bg-white rounded shadow p-4 lg:p-6 text-center text-gray-500">
        Тренировка на {{ selectedDate }} не найдена
      </div>
    </div>

    <!-- Модальное окно статистики пользователя -->
    <div
      v-if="selectedUserStats"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
      @click="selectedUserStats = null"
    >
      <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4" @click.stop>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">Статистика пользователя</h3>
          <button @click="selectedUserStats = null" class="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <div v-if="selectedUserStats.user_info" class="space-y-4">
          <div class="flex items-center gap-3">
            <User v-if="selectedUserStats.user_info.is_guest" class="w-5 h-5 text-blue-600" />
            <span class="font-medium text-gray-900">
              {{ selectedUserStats.user_info.username 
                ? '@' + selectedUserStats.user_info.username 
                : selectedUserStats.user_info.first_name + ' ' + (selectedUserStats.user_info.last_name || '') }}
            </span>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-50 rounded p-3 text-center">
              <p class="text-sm text-gray-500">Всего записей</p>
              <p class="text-2xl font-bold text-gray-900">{{ selectedUserStats.stats?.total_trainings || 0 }}</p>
            </div>
            <div class="bg-green-50 rounded p-3 text-center">
              <p class="text-sm text-gray-500">Посещено</p>
              <p class="text-2xl font-bold text-green-600">{{ selectedUserStats.stats?.attended_trainings || 0 }}</p>
            </div>
            <div class="bg-yellow-50 rounded p-3 text-center">
              <p class="text-sm text-gray-500">В ожидании</p>
              <p class="text-2xl font-bold text-yellow-600">{{ selectedUserStats.stats?.waitlist_count || 0 }}</p>
            </div>
            <div class="bg-gray-50 rounded p-3 text-center">
              <p class="text-sm text-gray-500">Как гость</p>
              <p class="text-2xl font-bold text-gray-900">{{ selectedUserStats.stats?.guests_trainings || 0 }}</p>
            </div>
          </div>

          <div class="text-sm text-gray-500">
            Период: {{ selectedUserStats.date_range?.from }} — {{ selectedUserStats.date_range?.to }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { BadgeCheck, User, BarChart3 } from 'lucide-vue-next'

const authStore = useAuthStore()

const periods = [
  { value: 'day', label: 'День' },
  { value: 'week', label: 'Неделя' },
  { value: 'month', label: 'Месяц' },
  { value: 'all', label: 'Всё время' }
]

const tabs = [
  { id: 'overview', label: 'Тренировки' },
  { id: 'games', label: 'Игры' },
  { id: 'top_users', label: 'Топ пользователей' },
  { id: 'by_date', label: 'По дате' }
]

const selectedPeriod = ref('week')
const activeTab = ref('overview')
const selectedDate = ref('')

const overviewStats = ref({})
const gamesStats = ref({})
const topUsers = ref([])
const totalEvents = ref(0)
const trainingsCount = ref(0)
const gamesCount = ref(0)
const trainingDetails = ref({})
const selectedUserStats = ref(null)

async function loadAllStats() {
  await loadOverviewStats()
  await loadGamesStats()
  await loadTopUsers()
}

async function loadOverviewStats() {
  try {
    const response = await fetch(`/api/admin/training-stats/overview?period=${selectedPeriod.value}`, {
      credentials: 'include'
    })
    if (response.ok) {
      overviewStats.value = await response.json()
    }
  } catch (error) {
    console.error('Error loading overview stats:', error)
  }
}

async function loadGamesStats() {
  try {
    const response = await fetch(`/api/admin/game-stats/overview?period=${selectedPeriod.value}`, {
      credentials: 'include'
    })
    if (response.ok) {
      gamesStats.value = await response.json()
    }
  } catch (error) {
    console.error('Error loading games stats:', error)
  }
}

async function loadTopUsers() {
  try {
    const response = await fetch(`/api/admin/training-stats/top-users?limit=50&period=${selectedPeriod.value}`, {
      credentials: 'include'
    })
    if (response.ok) {
      const data = await response.json()
      topUsers.value = data.users || []
      totalEvents.value = data.total_events || 0
      trainingsCount.value = data.trainings_count || 0
      gamesCount.value = data.games_count || 0
    }
  } catch (error) {
    console.error('Error loading top users:', error)
  }
}

async function loadTrainingDetails() {
  if (!selectedDate.value) {
    trainingDetails.value = {}
    return
  }

  try {
    const response = await fetch(`/api/admin/training-stats/details?training_date=${selectedDate.value}`, {
      credentials: 'include'
    })
    if (response.ok) {
      trainingDetails.value = await response.json()
    } else {
      trainingDetails.value = {}
    }
  } catch (error) {
    console.error('Error loading training details:', error)
    trainingDetails.value = {}
  }
}

async function showUserStats(telegramId) {
  try {
    const response = await fetch(`/api/admin/training-stats/user/${telegramId}?period=${selectedPeriod.value}`, {
      credentials: 'include'
    })
    if (response.ok) {
      selectedUserStats.value = await response.json()
    }
  } catch (error) {
    console.error('Error loading user stats:', error)
  }
}

// Устанавливаем сегодняшнюю дату по умолчанию
selectedDate.value = new Date().toISOString().split('T')[0]

onMounted(() => {
  loadAllStats()
})
</script>
