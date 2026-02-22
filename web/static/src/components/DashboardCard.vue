<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <span v-if="icon" class="text-xl">{{ icon }}</span>
        <slot name="title">Заголовок</slot>
      </h2>
      <slot name="header-action"></slot>
    </div>
    
    <div class="p-6">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  icon: {
    type: String,
    default: ''
  }
})
</script>
