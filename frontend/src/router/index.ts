import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'profiles',
          name: 'profiles',
          component: () => import('@/views/ProfilesView.vue'),
        },
        {
          path: 'profiles/:id',
          name: 'profile-detail',
          component: () => import('@/views/ProfileDetailView.vue'),
          props: true,
        },
        {
          path: 'my-profile',
          name: 'my-profile',
          component: () => import('@/views/MyProfileView.vue'),
        },
        {
          path: 'admin/tenants',
          name: 'tenants',
          component: () => import('@/views/TenantsView.vue'),
        },
        {
          path: 'admin/tenants/new',
          name: 'create-tenant',
          component: () => import('@/views/CreateTenantView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { public: true },
    },
  ],
})

// Navigation guard
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
})

export default router
