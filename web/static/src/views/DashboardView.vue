<template>
  <div class="flex flex-col gap-4 lg:gap-6">
    <!-- Контент для администраторов -->
    <template v-if="authStore.isAdmin">
      <!-- Краткая статистика -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6">
        <div class="bg-white rounded shadow p-4 lg:p-6">
          <div class="flex items-center gap-4">
            <Calendar class="w-12 h-12 text-teal-600" />
            <div>
              <p class="text-sm text-gray-500">Расписаний</p>
              <p class="text-2xl font-bold text-gray-900">{{ settingsStore.schedules.length }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded shadow p-4 lg:p-6">
          <div class="flex items-center gap-4">
            <BarChart3 class="w-12 h-12 text-blue-600" />
            <div>
              <p class="text-sm text-gray-500">Активных опросов</p>
              <p class="text-2xl font-bold text-gray-900">{{ settingsStore.activePolls.length }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded shadow p-4 lg:p-6">
          <div class="flex items-center gap-4">
            <Users class="w-12 h-12 text-purple-600" />
            <div>
              <p class="text-sm text-gray-500">Администраторов</p>
              <p class="text-2xl font-bold text-gray-900">{{ settingsStore.adminIds.length }}</p>
            </div>
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
              <p class="font-medium text-gray-900">Добавить расписание</p>
              <p class="text-sm text-gray-500">Создать новое расписание опросов</p>
            </div>
          </router-link>

          <router-link to="/dashboard/template" class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors">
            <ClipboardList class="w-10 h-10 text-teal-600" />
            <div>
              <p class="font-medium text-gray-900">Изменить шаблон</p>
              <p class="text-sm text-gray-500">Редактировать шаблон опроса</p>
            </div>
          </router-link>

          <router-link to="/dashboard/users" class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors">
            <Users class="w-10 h-10 text-teal-600" />
            <div>
              <p class="font-medium text-gray-900">Управление админами</p>
              <p class="text-sm text-gray-500">Добавить или удалить администратора</p>
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
                <span class="font-medium text-gray-700">Тренировка:</span> {{ formatDay(schedule.training_day) }}
                <span class="mx-2 text-gray-300">|</span>
                <span class="font-medium text-gray-700">Опрос:</span> {{ formatDay(schedule.poll_day) }}
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
import { onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import {
  Calendar,
  BarChart3,
  Users,
  ClipboardList,
  FileText,
  Link
} from 'lucide-vue-next'

const settingsStore = useSettingsStore()
const authStore = useAuthStore()

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

const getInitials = (user) => {
  if (!user) return '?'
  const first = user.first_name?.[0] || ''
  const last = user.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}

onMounted(async () => {
  await Promise.all([
    settingsStore.loadSchedules(),
    settingsStore.loadActivePolls(),
    settingsStore.loadAdminIds()
  ])
})
</script>
