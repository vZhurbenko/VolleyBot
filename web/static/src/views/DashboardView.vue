<template>
  <div class="space-y-6">
    <!-- Краткая статистика -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center text-2xl">
            📅
          </div>
          <div>
            <p class="text-sm text-gray-500">Расписаний</p>
            <p class="text-2xl font-bold text-gray-900">{{ settingsStore.schedules.length }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center text-2xl">
            📊
          </div>
          <div>
            <p class="text-sm text-gray-500">Активных опросов</p>
            <p class="text-2xl font-bold text-gray-900">{{ settingsStore.activePolls.length }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center text-2xl">
            👥
          </div>
          <div>
            <p class="text-sm text-gray-500">Администраторов</p>
            <p class="text-2xl font-bold text-gray-900">{{ settingsStore.adminIds.length }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Быстрые действия -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <router-link to="/admin/schedules" class="flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors">
          <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-xl">
            📅
          </div>
          <div>
            <p class="font-medium text-gray-900">Добавить расписание</p>
            <p class="text-sm text-gray-500">Создать новое расписание опросов</p>
          </div>
        </router-link>
        
        <router-link to="/admin/template" class="flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors">
          <div class="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center text-xl">
            📋
          </div>
          <div>
            <p class="font-medium text-gray-900">Изменить шаблон</p>
            <p class="text-sm text-gray-500">Редактировать шаблон опроса</p>
          </div>
        </router-link>
        
        <router-link to="/admin/admins" class="flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors">
          <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center text-xl">
            👥
          </div>
          <div>
            <p class="font-medium text-gray-900">Управление админами</p>
            <p class="text-sm text-gray-500">Добавить или удалить администратора</p>
          </div>
        </router-link>
        
        <router-link to="/admin/polls" class="flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors">
          <div class="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center text-xl">
            📈
          </div>
          <div>
            <p class="font-medium text-gray-900">Активные опросы</p>
            <p class="text-sm text-gray-500">Просмотр текущих опросов</p>
          </div>
        </router-link>
      </div>
    </div>
    
    <!-- Последние расписания -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Расписания</h2>
        <router-link to="/admin/schedules" class="text-sm text-blue-600 hover:underline">Все →</router-link>
      </div>
      
      <div v-if="settingsStore.schedules.length > 0" class="divide-y divide-gray-100">
        <div v-for="schedule in settingsStore.schedules.slice(0, 3)" :key="schedule.id" class="py-3 flex items-center justify-between">
          <div>
            <p class="font-medium text-gray-900">{{ schedule.name }}</p>
            <p class="text-sm text-gray-500">{{ schedule.training_day }} → {{ schedule.poll_day }}</p>
          </div>
          <span :class="['px-3 py-1 rounded-full text-xs font-medium', schedule.enabled ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700']">
            {{ schedule.enabled ? 'Активно' : 'Отключено' }}
          </span>
        </div>
      </div>
      <div v-else class="text-gray-500 text-center py-8">
        Нет расписаний
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

onMounted(async () => {
  await Promise.all([
    settingsStore.loadSchedules(),
    settingsStore.loadActivePolls(),
    settingsStore.loadAdminIds()
  ])
})
</script>
