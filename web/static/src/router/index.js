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
      path: '/dashboard',
      component: () => import('@/views/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue')
        },
        {
          path: 'calendar',
          name: 'calendar',
          component: () => import('@/views/CalendarView.vue')
        },
        {
          path: 'my-trainings',
          name: 'my-trainings',
          component: () => import('@/views/user/MyTrainings.vue')
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
          path: 'users',
          name: 'users',
          component: () => import('@/views/AdminsView.vue')
        },
        {
          path: 'invites',
          name: 'invites',
          component: () => import('@/views/InviteView.vue')
        },
        {
          path: 'trainings',
          name: 'trainings',
          component: () => import('@/views/TrainingsView.vue')
        }
      ]
    },
    {
      path: '/user',
      redirect: '/dashboard'
    },
    {
      path: '/admin',
      redirect: '/dashboard'
    },
    {
      path: '/invite/:code',
      name: 'invite-accept',
      component: () => import('@/views/InviteAcceptView.vue'),
      meta: { requiresAuth: false }  // Публичный доступ
    },
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
