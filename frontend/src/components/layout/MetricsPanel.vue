<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { getMetrics, type MetricsData } from '../../api/game'
import eventBus from '../../eventBus'

const isOpen = ref(false)
const loading = ref(false)
const data = ref<MetricsData | null>(null)

async function load() {
  loading.value = true
  try {
    data.value = await getMetrics()
  } finally {
    loading.value = false
  }
}

async function toggle() {
  isOpen.value = !isOpen.value
  if (isOpen.value) await load()
}

onMounted(() => eventBus.on('toggle-metrics', toggle))
onUnmounted(() => eventBus.off('toggle-metrics', toggle))
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="metrics-overlay" @click.self="isOpen = false">
      <div class="metrics-panel">
        <div class="metrics-header">
          <span class="metrics-title">Balance Metrics</span>
          <div class="metrics-header-actions">
            <button class="metrics-refresh" @click="load" :disabled="loading" title="Refresh">↻</button>
            <button class="metrics-close" @click="isOpen = false">&times;</button>
          </div>
        </div>

        <div class="metrics-body">
          <div v-if="loading" class="metrics-loading">Loading…</div>
          <template v-else-if="data">
            <div class="metrics-summary">
              {{ data.total_expeditions }} completed expedition{{ data.total_expeditions !== 1 ? 's' : '' }} on record
            </div>
            <div v-if="data.levels.length === 0" class="metrics-empty">
              No completed expeditions yet.
            </div>
            <table v-else class="metrics-table">
              <thead>
                <tr>
                  <th>Level</th>
                  <th>Runs</th>
                  <th>Avg Gold</th>
                  <th>Avg XP</th>
                  <th>Deaths/Run</th>
                  <th>Total Deaths</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in data.levels" :key="row.level">
                  <td class="lvl-cell">{{ row.level }}</td>
                  <td>{{ row.expeditions }}</td>
                  <td class="gold-cell">{{ row.avg_gold.toLocaleString() }} gp</td>
                  <td>{{ row.avg_xp.toLocaleString() }}</td>
                  <td :class="row.deaths_per_run >= 1 ? 'danger' : row.deaths_per_run >= 0.5 ? 'warn' : ''">
                    {{ row.deaths_per_run.toFixed(2) }}
                  </td>
                  <td>{{ row.total_deaths }}</td>
                </tr>
              </tbody>
            </table>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.metrics-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 80px;
  background: rgba(0, 0, 0, 0.5);
}

.metrics-panel {
  width: 620px;
  background: #0d0d0d;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8);
  font-family: var(--font-mono);
  font-size: 13px;
  color: #ccc;
}

.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid #1e1e1e;
}

.metrics-title {
  color: #a78bfa;
  font-weight: 700;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.metrics-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metrics-refresh,
.metrics-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  color: #555;
  font-size: 16px;
}

.metrics-refresh { font-size: 14px; }
.metrics-refresh:hover, .metrics-close:hover { color: #fff; }
.metrics-refresh:disabled { opacity: 0.4; cursor: default; }

.metrics-body {
  padding: 12px 14px;
}

.metrics-loading,
.metrics-empty {
  color: #555;
  padding: 12px 0;
  text-align: center;
}

.metrics-summary {
  color: #555;
  font-size: 11px;
  margin-bottom: 12px;
}

.metrics-table {
  width: 100%;
  border-collapse: collapse;
}

.metrics-table th {
  text-align: left;
  color: #555;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 8px 6px;
  border-bottom: 1px solid #1e1e1e;
}

.metrics-table td {
  padding: 6px 8px;
  border-bottom: 1px solid #161616;
}

.metrics-table tr:last-child td {
  border-bottom: none;
}

.lvl-cell {
  color: #a78bfa;
  font-weight: 700;
}

.gold-cell {
  color: #fbbf24;
}

.warn { color: #f59e0b; }
.danger { color: #ef4444; }
</style>
