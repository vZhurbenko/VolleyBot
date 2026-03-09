<template>
  <div class="flex min-h-screen bg-gradient-to-br from-slate-100 to-slate-200">
    <!-- Кнопка гамбургера для мобильных -->
    <button
      @click="toggleMenu"
      class="fixed top-4 left-4 z-30 lg:hidden p-2 rounded-lg bg-white shadow-md hover:bg-gray-50 transition-colors"
      aria-label="Открыть меню"
    >
      <Menu class="w-6 h-6 text-gray-700" />
    </button>

    <Sidebar />

    <div class="flex-1 flex flex-col min-w-0">
      <main class="flex-1 p-4 lg:p-6 pt-16 lg:pt-6 overflow-y-auto">
        <div class="max-w-7xl mx-auto">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { Menu } from 'lucide-vue-next'
import Sidebar from '@/components/Sidebar.vue'

const toggleMenu = () => {
  window.dispatchEvent(new CustomEvent('toggle-menu'))
}
</script>
