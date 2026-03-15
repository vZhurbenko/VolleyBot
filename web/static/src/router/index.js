import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      alias: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/dashboard',
      component: () => import('@/views/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'calendar',
          name: 'calendar',
          component: () => import('@/views/CalendarView.vue'),
        },
        {
          path: 'my-trainings',
          name: 'my-trainings',
          component: () => import('@/views/user/MyTrainings.vue'),
        },
        {
          path: 'template',
          name: 'template',
          component: () => import('@/views/TemplateView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'schedules',
          name: 'schedules',
          component: () => import('@/views/SchedulesView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'polls',
          name: 'polls',
          component: () => import('@/views/PollsView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/AdminsView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'invites',
          name: 'invites',
          component: () => import('@/views/InviteView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'trainings',
          name: 'trainings',
          component: () => import('@/views/TrainingsView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'stats',
          name: 'stats',
          component: () => import('@/views/StatsView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'games',
          name: 'games',
          component: () => import('@/views/GamesView.vue'),
        },
      ],
    },
    {
      path: '/user',
      redirect: '/dashboard/calendar',
    },
    {
      path: '/admin',
      redirect: '/dashboard',
    },
    {
      path: '/invite/:code',
      name: 'invite-accept',
      component: () => import('@/views/InviteAcceptView.vue'),
      meta: { requiresAuth: false }, // Публичный доступ
    },
    {
      path: '/t/:uuid',
      name: 'training-redirect',
      component: () => import('@/views/TrainingRedirectView.vue'),
    },
    {
      path: '/guest/training/:uuid',
      name: 'guest-training',
      component: () => import('@/views/guest/GuestTrainingView.vue'),
      meta: { requiresAuth: false }, // Авторизация проверяется внутри компонента
    },
  ],
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Публичные маршруты — пропускаем сразу
  if (
    to.path === '/' ||
    to.path === '/login' ||
    to.path.startsWith('/t/') ||
    to.path.startsWith('/guest/') ||
    to.path.startsWith('/invite/')
  ) {
    return next()
  }

  // Ждём завершения проверки авторизации (максимум 2 секунды)
  if (authStore.isLoading) {
    const maxWait = 2000
    const startTime = Date.now()
    while (authStore.isLoading && Date.now() - startTime < maxWait) {
      await new Promise(resolve => setTimeout(resolve, 100))
    }
  }

  // Для всех остальных маршрутов — проверяем авторизацию
  if (!authStore.isAuthenticated) {
    return next('/')
  }

  // Проверка прав администратора для защищённых маршрутов
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return next('/dashboard/calendar')
  }

  next()
})

export default router
