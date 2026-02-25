<template>
  <div class="fixed top-4 right-4 z-[100] space-y-2">
    <TransitionGroup name="toast">
      <div
        v-for="notification in notificationsStore.notifications"
        :key="notification.id"
        class="flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg min-w-[300px] max-w-md"
        :class="notification.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'"
      >
        <component
          :is="iconComponent"
          class="w-5 h-5 flex-shrink-0"
          :class="notification.type === 'success' ? 'text-green-600' : 'text-red-600'"
        />
        <p class="text-sm flex-1" :class="notification.type === 'success' ? 'text-green-800' : 'text-red-800'">
          {{ notification.message }}
        </p>
        <button
          @click="notificationsStore.removeNotification(notification.id)"
          class="w-6 h-6 flex items-center justify-center rounded hover:bg-black/5 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import { CheckCircle, XCircle } from 'lucide-vue-next'

const notificationsStore = useNotificationsStore()

const iconComponent = computed(() => {
  const notification = notificationsStore.notifications[0]
  return notification?.type === 'success' ? CheckCircle : XCircle
})
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
