<template>
  <div class="flex flex-col gap-4 lg:gap-6">
    <!-- Контент для администраторов -->
    <template v-if="authStore.isAdmin">
      <!-- Краткая статистика -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        <div class="bg-white rounded shadow p-4 lg:p-6 text-center">
          <p class="text-sm text-gray-500 mb-4">Администраторов</p>
          <div class="flex items-center justify-center gap-3">
            <Users class="w-10 h-10 text-purple-600" />
            <p class="text-3xl font-bold text-gray-900">{{ stats.adminCount }}</p>
          </div>
        </div>

        <div class="bg-white rounded shadow p-4 lg:p-6 text-center">
          <p class="text-sm text-gray-500 mb-4">Всего пользователей</p>
          <div class="flex items-center justify-center gap-3">
            <User class="w-10 h-10 text-blue-600" />
            <p class="text-3xl font-bold text-gray-900">{{ stats.usersCount }}</p>
          </div>
        </div>

        <div class="bg-white rounded shadow p-4 lg:p-6 text-center">
          <p class="text-sm text-gray-500 mb-4">Расписаний</p>
          <div class="flex items-center justify-center gap-3">
            <Calendar class="w-10 h-10 text-teal-600" />
            <p class="text-3xl font-bold text-gray-900">{{ stats.schedulesCount }}</p>
          </div>
        </div>

        <div class="bg-white rounded shadow p-4 lg:p-6 text-center">
          <p class="text-sm text-gray-500 mb-4">Записей за 30 дней</p>
          <div class="flex items-center justify-center gap-3">
            <BarChart3 class="w-10 h-10 text-green-600" />
            <p class="text-3xl font-bold text-gray-900">{{ stats.registrationsCount }}</p>
          </div>
        </div>
      </div>

      <!-- Быстрые действия -->
      <div class="bg-white rounded shadow p-4 lg:p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <router-link to="/dashboard/schedules" class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors">
            <Calendar class="w-10 h-10 text-teal-600" />
            <div>
              <p class="font-medium text-gray-900">Расписания</p>
              <p class="text-sm text-gray-500">Управление расписаниями опросов</p>
            </div>
          </router-link>

          <router-link to="/dashboard/polls" class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors">
            <Radio class="w-10 h-10 text-teal-600" />
            <div>
              <p class="font-medium text-gray-900">Опросы</p>
              <p class="text-sm text-gray-500">Управление активными опросами</p>
            </div>
          </router-link>

          <router-link to="/dashboard/users" class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors">
            <Users class="w-10 h-10 text-teal-600" />
            <div>
              <p class="font-medium text-gray-900">Пользователи</p>
              <p class="text-sm text-gray-500">Управление пользователями</p>
            </div>
          </router-link>

          <router-link to="/dashboard/invites" class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors">
            <Link class="w-10 h-10 text-teal-600" />
            <div>
              <p class="font-medium text-gray-900">Приглашения</p>
              <p class="text-sm text-gray-500">Создать коды приглашений</p>
            </div>
          </router-link>
        </div>
      </div>

      <!-- Последние активности -->
      <div class="bg-white rounded shadow p-4 lg:p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Последние записи</h2>
          <span class="text-sm text-gray-500">за 30 дней</span>
        </div>

        <div v-if="stats.recentActivities.length > 0" class="divide-y divide-gray-100">
          <div v-for="activity in stats.recentActivities" :key="activity.registered_at" class="py-3 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center text-teal-700 font-semibold text-sm">
                {{ getUserInitials(activity) }}
              </div>
              <div>
                <p class="font-medium text-gray-900">{{ getUserName(activity) }}</p>
                <p class="text-sm text-gray-500">
                  {{ formatDate(activity.training_date) }}, {{ activity.training_time }}
                </p>
              </div>
            </div>
            <span :class="['px-3 py-1 rounded text-xs font-medium', getStatusClass(activity.status)]">
              {{ getStatusText(activity.status) }}
            </span>
          </div>
        </div>
        <div v-else class="text-gray-500 text-center py-8">
          Нет записей за последние 30 дней
        </div>
      </div>

      <!-- Последние расписания -->
      <div class="bg-white rounded shadow p-4 lg:p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Расписания</h2>
          <router-link to="/dashboard/schedules" class="text-sm text-teal-600 hover:underline">Все →</router-link>
        </div>

        <div v-if="settingsStore.schedules.length > 0" class="divide-y divide-gray-100">
          <div v-for="schedule in settingsStore.schedules.slice(0, 3)" :key="schedule.id" class="py-3 flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-900">{{ schedule.name }}</p>
              <p class="text-sm text-gray-500">
                <span class="font-medium text-gray-700">Тренировка:</span> {{ formatDay(schedule.training_day) }}, {{ schedule.start_time }} - {{ schedule.end_time }}, {{ schedule.location }}
                <span class="mx-2 text-gray-300">|</span>
                <span class="font-medium text-gray-700">Опрос:</span> {{ formatDay(getPollDay(schedule.training_day)) }}
              </p>
            </div>
            <span :class="['px-3 py-1 rounded text-xs font-medium', schedule.enabled ? 'bg-teal-100 text-teal-700' : 'bg-red-100 text-red-700']">
              {{ schedule.enabled ? 'Активно' : 'Отключено' }}
            </span>
          </div>
        </div>
        <div v-else class="text-gray-500 text-center py-8">
          Нет расписаний
        </div>
      </div>
    </template>

    <!-- Контент для обычных пользователей -->
    <template v-else>
      <div class="bg-white rounded shadow p-4 lg:p-6">
        <div class="flex items-center gap-4">
          <img
            v-if="authStore.user?.photo_url"
            :src="authStore.user.photo_url"
            alt=""
            class="w-16 h-16 rounded-full"
          />
          <div
            v-else
            class="w-16 h-16 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold text-xl"
          >
            {{ getInitials(authStore.user) }}
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-900">
              {{ authStore.user?.first_name }} {{ authStore.user?.last_name || '' }}
            </h2>
            <p v-if="authStore.user?.username" class="text-sm text-gray-500">@{{ authStore.user.username }}</p>
            <p class="text-sm text-gray-500">ID: {{ authStore.user?.telegram_id }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded shadow p-4 lg:p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <router-link to="/dashboard/calendar" class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors">
            <Calendar class="w-10 h-10 text-teal-600" />
            <div>
              <p class="font-medium text-gray-900">Календарь тренировок</p>
              <p class="text-sm text-gray-500">Посмотреть расписание</p>
            </div>
          </router-link>

          <router-link to="/dashboard/my-trainings" class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors">
            <FileText class="w-10 h-10 text-teal-600" />
            <div>
              <p class="font-medium text-gray-900">Мои записи</p>
              <p class="text-sm text-gray-500">Управление записями</p>
            </div>
          </router-link>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import {
  Calendar,
  BarChart3,
  Users,
  User,
  FileText,
  Link,
  Radio
} from 'lucide-vue-next'

const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const stats = ref({
  adminCount: 0,
  usersCount: 0,
  schedulesCount: 0,
  registrationsCount: 0,
  recentActivities: []
})

const days = {
  monday: 'Пн',
  tuesday: 'Вт',
  wednesday: 'Ср',
  thursday: 'Чт',
  friday: 'Пт',
  saturday: 'Сб',
  sunday: 'Вс'
}

const dayOrder = {
  monday: 0,
  tuesday: 1,
  wednesday: 2,
  thursday: 3,
  friday: 4,
  saturday: 5,
  sunday: 6
}

const formatDay = (day) => days[day] || day

// Вычисляем день опроса (за 3 дня до тренировки)
const getPollDay = (trainingDay) => {
  if (!trainingDay) return ''
  const trainingDayIndex = dayOrder[trainingDay]
  const pollDayIndex = (trainingDayIndex - 3 + 7) % 7
  return Object.keys(dayOrder).find(key => dayOrder[key] === pollDayIndex) || trainingDay
}

const getInitials = (user) => {
  if (!user) return '?'
  const first = user.first_name?.[0] || ''
  const last = user.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}

const getUserInitials = (activity) => {
  if (!activity) return '?'
  const first = activity.first_name?.[0] || ''
  const last = activity.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}

const getUserName = (activity) => {
  if (!activity) return ''
  const first = activity.first_name || ''
  const last = activity.last_name || ''
  return `${first} ${last}`.trim() || activity.username || 'Аноним'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
}

const getStatusClass = (status) => {
  if (status === 'registered') return 'bg-teal-100 text-teal-700'
  if (status === 'waitlist') return 'bg-yellow-100 text-yellow-700'
  return 'bg-gray-100 text-gray-700'
}

const getStatusText = (status) => {
  if (status === 'registered') return 'Записан'
  if (status === 'waitlist') return 'Ожидание'
  return status || 'Неизвестно'
}

const loadStats = async () => {
  try {
    const response = await fetch('/api/admin/stats', {
      credentials: 'include'
    })
    
    if (response.ok) {
      const data = await response.json()
      stats.value = {
        adminCount: data.admin_count || 0,
        usersCount: data.users_count || 0,
        schedulesCount: data.schedules_count || 0,
        registrationsCount: data.registrations_count || 0,
        recentActivities: data.recent_activities || []
      }
    }
  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

onMounted(async () => {
  await Promise.all([
    loadStats(),
    settingsStore.loadSchedules()
  ])
})
</script>
