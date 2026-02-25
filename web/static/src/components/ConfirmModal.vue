<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="fixed inset-0 z-[99] flex items-center justify-center p-4">
        <!-- Overlay -->
        <div
          class="absolute inset-0 bg-black/50"
          @click="handleCancel"
        />

        <!-- Modal -->
        <div
          class="relative bg-white rounded-lg shadow-xl w-full max-w-md"
          role="dialog"
          aria-modal="true"
        >
          <div class="p-6">
            <div class="flex items-start gap-4">
              <!-- Icon -->
              <div
                class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                :class="mode === 'danger' ? 'bg-red-100' : 'bg-blue-100'"
              >
                <component
                  :is="iconComponent"
                  class="w-5 h-5"
                  :class="mode === 'danger' ? 'text-red-600' : 'text-blue-600'"
                />
              </div>

              <!-- Content -->
              <div class="flex-1">
                <h3 class="text-lg font-semibold text-gray-900 mb-2">
                  {{ title }}
                </h3>
                <p class="text-sm text-gray-600">
                  {{ message }}
                </p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex justify-end gap-3 mt-6">
              <button
                @click="handleCancel"
                class="px-4 py-2 rounded font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
              >
                {{ cancelText }}
              </button>
              <button
                @click="handleConfirm"
                class="px-4 py-2 rounded font-medium transition-colors"
                :class="mode === 'danger' ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-teal-600 text-white hover:bg-teal-700'"
              >
                {{ confirmText }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, watch } from 'vue'
import { AlertTriangle, Info } from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Подтверждение'
  },
  message: {
    type: String,
    required: true
  },
  mode: {
    type: String,
    default: 'danger',
    validator: (value) => ['danger', 'info'].includes(value)
  },
  cancelText: {
    type: String,
    default: 'Отмена'
  },
  confirmText: {
    type: String,
    default: 'Подтвердить'
  }
})

const emit = defineEmits(['confirm', 'cancel', 'close'])

const iconComponent = computed(() => {
  return props.mode === 'danger' ? AlertTriangle : Info
})

const handleConfirm = () => {
  emit('confirm')
  emit('close')
}

const handleCancel = () => {
  emit('cancel')
  emit('close')
}

// Закрытие по ESC
watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      const handleEsc = (e) => {
        if (e.key === 'Escape') {
          handleCancel()
        }
      }
      document.addEventListener('keydown', handleEsc)
      return () => document.removeEventListener('keydown', handleEsc)
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .relative,
.modal-leave-to .relative {
  opacity: 0;
  transform: scale(0.95);
}
</style>
