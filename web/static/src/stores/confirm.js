import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useConfirmStore = defineStore('confirm', () => {
  const isOpen = ref(false)
  const title = ref('Подтверждение')
  const message = ref('')
  const mode = ref('danger')
  const confirmText = ref('Подтвердить')
  
  let resolvePromise = null

  const open = (options) => {
    return new Promise((resolve) => {
      title.value = options.title || 'Подтверждение'
      message.value = options.message
      mode.value = options.mode || 'danger'
      confirmText.value = options.confirmText || 'Подтвердить'
      resolvePromise = resolve
      isOpen.value = true
    })
  }

  const resolve = (value) => {
    if (resolvePromise) {
      resolvePromise(value)
      resolvePromise = null
    }
  }

  const close = () => {
    isOpen.value = false
    if (resolvePromise) {
      resolvePromise(false)
      resolvePromise = null
    }
  }

  // Удобные методы для разных типов подтверждений
  const danger = (message, options = {}) => open({
    message,
    mode: 'danger',
    confirmText: 'Удалить',
    ...options
  })

  const info = (message, options = {}) => open({
    message,
    mode: 'info',
    confirmText: 'Подтвердить',
    ...options
  })

  return {
    isOpen,
    title,
    message,
    mode,
    confirmText,
    open,
    close,
    resolve,
    danger,
    info
  }
})
