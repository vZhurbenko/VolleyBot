<template>
  <div class="flex min-h-screen bg-gradient-to-br from-slate-100 to-slate-200">
    <Sidebar />

    <div class="flex-1 flex flex-col min-w-0">
      <main class="flex-1 p-4 lg:p-6 overflow-auto">
        <div class="max-w-7xl mx-auto">
          <Topbar>
            <template #title>{{ pageTitle }}</template>
          </Topbar>

          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import Topbar from '@/components/Topbar.vue'

const route = useRoute()

const pageTitle = computed(() => {
  const titles = {
    dashboard: 'Панель управления',
    template: 'Шаблон опроса',
    schedules: 'Расписания',
    polls: 'Опросы',
    admins: 'Администраторы'
  }
  return titles[route.name] || 'Team R Admin'
})
</script>
