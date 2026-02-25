<template>
  <RouterView />
  <Toast />
  <ConfirmModal
    :is-open="confirmStore.isOpen"
    :title="confirmStore.title"
    :message="confirmStore.message"
    :mode="confirmStore.mode"
    :confirm-text="confirmStore.confirmText"
    @confirm="confirmStore.resolve(true)"
    @cancel="confirmStore.resolve(false)"
    @close="confirmStore.close"
  />
</template>

<script setup>
import Toast from '@/components/Toast.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import { useConfirmStore } from '@/stores/confirm'

const confirmStore = useConfirmStore()
</script>
