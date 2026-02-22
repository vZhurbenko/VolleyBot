import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: () => import('@/views/LoginView.vue')
    },
    {
      path: '/admin',
      component: () => import('@/views/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue')
        },
        {
          path: 'template',
          name: 'template',
          component: () => import('@/views/TemplateView.vue')
        },
        {
          path: 'schedules',
          name: 'schedules',
          component: () => import('@/views/SchedulesView.vue')
        },
        {
          path: 'polls',
          name: 'polls',
          component: () => import('@/views/PollsView.vue')
        },
        {
          path: 'admins',
          name: 'admins',
          component: () => import('@/views/AdminsView.vue')
        }
      ]
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth) {
    if (authStore.isLoading) {
      await authStore.checkAuth()
    }
    
    if (!authStore.isAuthenticated) {
      return next('/')
    }
  }
  
  next()
})

export default router
