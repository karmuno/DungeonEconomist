<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as expeditionsApi from '../api/expeditions'
import type { ExpeditionSummaryDetail } from '../api/expeditions'
import { useNotificationsStore } from '../stores/notifications'
import { formatCurrency } from '../utils/currency'
import { formatGameDay } from '../utils/calendar'
import ProgressBar from '../components/shared/ProgressBar.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const router = useRouter()
const route = useRoute()
const notifications = useNotificationsStore()

const summary = ref<ExpeditionSummaryDetail | null>(null)
const loading = ref(true)

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    summary.value = await expeditionsApi.getSummary(id)
  } catch {
    notifications.add('Failed to load expedition summary', 'error')
    router.push('/')
  } finally {
    loading.value = false
  }
})

function lootCopper(total: number): { gold: number; silver: number; copper: number } {
  const copper_total = total * 100
  return {
    gold: Math.floor(copper_total / 100),
    silver: Math.floor((copper_total % 100) / 10),
    copper: copper_total % 10,
  }
}
</script>

<template>
  <div>
    <h1 class="mb-3">Expedition Summary</h1>

    <LoadingSpinner v-if="loading" />
    <template v-else-if="summary">
      <div class="card mb-3">
        <div class="flex flex-between mb-2">
          <h2>{{ summary.party_name }}</h2>
          <span class="badge">{{ summary.result }}</span>
        </div>
        <p class="text-muted">
          {{ formatGameDay(summary.start_day) }} &mdash; {{ formatGameDay(summary.return_day) }}
          ({{ summary.duration_days }} days)
        </p>
      </div>

      <!-- Party Member Results -->
      <div class="card mb-3">
        <h3 class="mb-2">Party Members</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Class</th>
              <th>Level</th>
              <th>Status</th>
              <th>HP</th>
              <th>XP Gained</th>
              <th>Wealth</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="member in summary.member_results"
              :key="member.name"
              :class="{ 'text-danger': !member.alive }"
            >
              <td>{{ member.name }}</td>
              <td>{{ member.adventurer_class }}</td>
              <td>{{ member.level }}</td>
              <td>
                <span v-if="member.alive" class="badge badge-success">Alive</span>
                <span v-else class="badge badge-danger">Dead</span>
              </td>
              <td>
                <ProgressBar
                  v-if="member.alive"
                  :value="member.hp_current"
                  :max="member.hp_max"
                />
                <span v-else>&mdash;</span>
              </td>
              <td>+{{ member.xp_gained }}</td>
              <td class="text-gold">{{ formatCurrency(member.gold, member.silver, member.copper) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Rewards -->
      <div class="stats-grid mb-3">
        <div class="stat-card">
          <div class="stat-value text-gold">
            {{ formatCurrency(lootCopper(summary.total_loot).gold, lootCopper(summary.total_loot).silver, lootCopper(summary.total_loot).copper) }}
          </div>
          <div class="stat-label">Total Loot</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ summary.total_xp }}</div>
          <div class="stat-label">Total XP</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formatGameDay(summary.estimated_readiness_day) }}</div>
          <div class="stat-label">Est. Ready By</div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-1">
        <button class="btn btn-primary" @click="router.push('/adventurers')">
          Examine Roster
        </button>
        <button class="btn btn-secondary" @click="router.push('/')">
          Back to Dashboard
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.badge-success {
  background: var(--accent-green-dark, #2d5a27);
  color: var(--accent-green, #4ade80);
}

.badge-danger {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}
</style>
