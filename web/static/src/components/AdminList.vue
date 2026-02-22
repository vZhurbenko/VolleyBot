<template>
  <div class="admins-list">
    <div class="add-admin-form">
      <div class="form-group">
        <label class="form-label">Добавить администратора</label>
        <div class="input-group">
          <input 
            v-model="newAdminId" 
            type="number" 
            class="form-input"
            placeholder="Telegram ID"
          />
          <button @click="handleAdd" class="btn btn-primary">
            Добавить
          </button>
        </div>
      </div>
    </div>
    
    <div class="admin-items">
      <div v-for="id in adminIds" :key="id" class="admin-item">
        <span class="admin-id">ID: {{ id }}</span>
        <div class="admin-actions">
          <span class="tag tag-enabled">Админ</span>
          <button @click="$emit('remove', id)" class="btn btn-danger btn-small">
            ✕
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  adminIds: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['add', 'remove'])

const newAdminId = ref('')

const handleAdd = () => {
  if (newAdminId.value) {
    emit('add', parseInt(newAdminId.value))
    newAdminId.value = ''
  }
}
</script>

<style scoped>
.admins-list {
  @apply space-y-4;
}

.add-admin-form {
  @apply pb-4 border-b border-gray-100;
}

.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-sm font-medium text-gray-700;
}

.input-group {
  @apply flex gap-2;
}

.form-input {
  @apply flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors;
}

.admin-items {
  @apply space-y-2;
}

.admin-item {
  @apply flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg;
}

.admin-id {
  @apply font-mono text-sm text-gray-700;
}

.admin-actions {
  @apply flex items-center gap-2;
}

.tag {
  @apply px-3 py-1 rounded-full text-xs font-medium;
}

.tag-enabled {
  @apply bg-green-100 text-green-700;
}

.btn {
  @apply px-3 py-2 rounded-lg font-medium transition-colors;
}

.btn-primary {
  @apply bg-gray-900 text-white hover:bg-gray-800;
}

.btn-danger {
  @apply bg-red-500 text-white hover:bg-red-600;
}

.btn-small {
  @apply px-2 py-1 text-sm;
}
</style>
