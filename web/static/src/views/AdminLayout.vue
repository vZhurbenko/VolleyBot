<template>
  <div class="flex h-screen bg-gradient-to-br from-slate-100 to-slate-200 overflow-hidden">
    <Sidebar />

    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <main class="flex-1 p-4 lg:p-6 overflow-y-auto">
        <div class="max-w-7xl mx-auto">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
</script>
