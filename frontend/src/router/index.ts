import { createRouter, createWebHistory } from 'vue-router'
import { get } from '../api/client'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/new-game',
      name: 'new-game',
      component: () => import('../views/NewGameView.vue'),
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
  ],
})

router.beforeEach(async (to) => {
  if (to.name === 'new-game') return true
  try {
    const status = await get<{ exists: boolean }>('/game/status')
    if (!status.exists) {
      return { name: 'new-game' }
    }
  } catch {
    // If the API is unreachable, let the user through
  }
  return true
})

export default router
