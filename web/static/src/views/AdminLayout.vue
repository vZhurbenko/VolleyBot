<template>
  <div class="flex h-screen bg-gradient-to-br from-slate-100 to-slate-200">
    <!-- Сайдбар с h-full, чтобы занимал всю высоту -->
    <div class="flex-shrink-0">
      <Sidebar @menu-change="isMenuOpen = $event" />
    </div>

    <!-- Кнопка гамбургера для мобильных (скрывается при открытом меню) -->
    <button
      v-show="!isMenuOpen"
      @click="toggleMenu"
      class="fixed top-4 left-4 z-[60] lg:hidden p-2 rounded bg-white shadow hover:bg-gray-100 transition-colors"
      aria-label="Открыть меню"
    >
      <Menu class="w-6 h-6 text-gray-700" />
    </button>

    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <main class="flex-1 overflow-y-auto p-4 lg:p-6 pt-16 lg:pt-6">
        <div class="max-w-7xl mx-auto w-full">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Menu } from 'lucide-vue-next'
import Sidebar from '@/components/Sidebar.vue'

const isMenuOpen = ref(false)

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
  window.dispatchEvent(new CustomEvent('toggle-menu'))
}
</script>
