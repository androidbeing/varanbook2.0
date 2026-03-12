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
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('@/views/ForgotPasswordView.vue'),
      meta: { public: true },
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('@/views/ResetPasswordView.vue'),
      meta: { public: true },
    },
    {
      path: '/privacy-policy',
      name: 'privacy-policy',
      component: () => import('@/views/PrivacyPolicyView.vue'),
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
          path: 'shortlisted',
          name: 'shortlisted',
          component: () => import('@/views/ShortlistedView.vue'),
        },
        {
          path: 'my-interests',
          name: 'my-interests',
          component: () => import('@/views/MyInterestsView.vue'),
        },
        {
          path: 'my-profile',
          name: 'my-profile',
          component: () => import('@/views/MyProfileView.vue'),
        },
        {
          path: 'admin/profile',
          name: 'admin-profile',
          component: () => import('@/views/AdminProfileView.vue'),
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
        {
          path: 'admin/onboard-members',
          name: 'onboard-members',
          component: () => import('@/views/OnboardMembersView.vue'),
          meta: { adminOnly: true },
        },
        {
          path: 'admin/shortlists',
          name: 'admin-shortlists',
          component: () => import('@/views/AdminShortlistsView.vue'),
          meta: { adminOnly: true },
        },
        {
          path: 'admin/membership',
          name: 'admin-membership',
          component: () => import('@/views/AdminMembershipView.vue'),
          meta: { adminOnly: true },
        },
        {
          path: 'membership',
          name: 'membership',
          component: () => import('@/views/MembershipPlansView.vue'),
        },
        {
          path: 'change-password',
          name: 'change-password',
          component: () => import('@/views/ChangePasswordView.vue'),
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
