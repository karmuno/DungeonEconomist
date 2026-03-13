import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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
      path: '/expeditions',
      name: 'expeditions',
      component: () => import('../views/ExpeditionsView.vue'),
    },
  ],
})

export default router
