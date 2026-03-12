<template>
  <div class="mb-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <!-- Кнопка меню для мобильных -->
        <button
          @click="toggleMenu"
          class="lg:hidden p-2 rounded hover:bg-gray-100 transition-colors"
        >
          <span class="text-xl">☰</span>
        </button>

        <h1 class="text-lg lg:text-xl font-bold text-gray-900">
          <slot name="title">Team R Admin</slot>
        </h1>
      </div>
    </div>
  </div>
</template>

<script setup>
const toggleMenu = () => {
  window.dispatchEvent(new CustomEvent('toggle-menu'))
}
</script>
