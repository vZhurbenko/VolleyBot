<template>
  <button
    type="button"
    @click="handleClick"
    class="relative w-12 h-6 rounded-full transition-colors"
    :class="modelValue ? 'bg-teal-600' : 'bg-gray-300'"
    :disabled="disabled"
    :aria-pressed="modelValue"
  >
    <span
      class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform shadow-sm"
      :class="modelValue ? 'translate-x-6' : 'translate-x-0'"
    />
  </button>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle'])

const handleClick = (event) => {
  event.stopPropagation()
  if (!props.disabled) {
    emit('toggle')
  }
}
</script>
