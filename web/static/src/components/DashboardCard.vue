<template>
  <div class="card">
    <div class="card-header">
      <h2 class="card-title">
        <span v-if="icon" class="card-icon">{{ icon }}</span>
        <slot name="title">Заголовок</slot>
      </h2>
      <slot name="header-action"></slot>
    </div>
    
    <div class="card-content">
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

<style scoped>
.card {
  @apply bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden;
}

.card-header {
  @apply px-6 py-4 border-b border-gray-100 flex items-center justify-between;
}

.card-title {
  @apply text-lg font-semibold text-gray-900 flex items-center gap-2;
}

.card-icon {
  @apply text-xl;
}

.card-content {
  @apply p-6;
}
</style>
