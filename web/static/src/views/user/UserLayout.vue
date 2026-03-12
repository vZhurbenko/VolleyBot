<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200">
    <!-- Верхняя навигация -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Логотип и название -->
          <div class="flex items-center gap-3">
            <img :src="logo" alt="Team R Logo" class="w-8 h-8" />
            <span class="text-lg font-bold text-gray-900">Team R</span>
          </div>

          <!-- Навигация -->
          <nav class="flex items-center gap-1">
            <router-link
              to="/user/calendar"
              class="px-4 py-2 rounded text-sm font-medium transition-colors"
              :class="
                $route.name === 'user-calendar'
                  ? 'bg-teal-50 text-teal-700'
                  : 'text-gray-600 hover:bg-gray-50'
              "
            >
              Календарь
            </router-link>
            <router-link
              to="/user/my-trainings"
              class="px-4 py-2 rounded text-sm font-medium transition-colors"
              :class="
                $route.name === 'my-trainings'
                  ? 'bg-teal-50 text-teal-700'
                  : 'text-gray-600 hover:bg-gray-50'
              "
            >
              Мои тренировки
            </router-link>
            <router-link
              v-if="authStore.isAdmin"
              to="/admin"
              class="px-4 py-2 rounded text-sm font-medium transition-colors text-gray-600 hover:bg-gray-50"
            >
              Админка
            </router-link>
          </nav>
        </div>
      </div>
    </header>

    <!-- Контент -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import logo from '@/img/logo.svg'

const router = useRouter()
const authStore = useAuthStore()
</script>
