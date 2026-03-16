import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { public: true },
    },
    {
      path: '/keeps',
      name: 'keeps',
      component: () => import('../views/KeepSelectView.vue'),
      meta: { requiresAuth: true, noKeep: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
    },
    {
      path: '/adventurers',
      name: 'adventurers',
      component: () => import('../views/AdventurersView.vue'),
    },
    {
      path: '/parties',
      name: 'parties',
      component: () => import('../views/PartiesView.vue'),
    },
    {
      path: '/form-party',
      name: 'form-party',
      component: () => import('../views/PartyFormationView.vue'),
    },
    {
      path: '/expeditions',
      name: 'expeditions',
      component: () => import('../views/ExpeditionsView.vue'),
    },
    {
      path: '/launch-expedition/:partyId?',
      name: 'launch-expedition',
      component: () => import('../views/ExpeditionLaunchView.vue'),
    },
    {
      path: '/expedition/:id/summary',
      name: 'expedition-summary',
      component: () => import('../views/ExpeditionSummaryView.vue'),
    },
    {
      path: '/expedition/:id/choice',
      name: 'expedition-choice',
      component: () => import('../views/ExpeditionChoiceView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const token = localStorage.getItem('token')
  const keepId = localStorage.getItem('keepId')

  // Public pages (login, register) — always accessible
  if (to.meta?.public) {
    return true
  }

  // No token → redirect to login
  if (!token) {
    return { name: 'login' }
  }

  // Keeps page doesn't require a keep selection
  if (to.meta?.noKeep) {
    return true
  }

  // Has token but no keep selected → redirect to keep selection
  if (!keepId) {
    return { name: 'keeps' }
  }

  return true
})

export default router
