import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
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

export default router
