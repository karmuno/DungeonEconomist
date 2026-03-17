<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboardStats } from '../api/game'
import * as partiesApi from '../api/parties'
import * as buildingsApi from '../api/buildings'
import type { DashboardStats } from '../types'
import { useGameTimeStore } from '../stores/gameTime'
import { useNotificationsStore } from '../stores/notifications'
import { formatCurrency } from '../utils/currency'
import ProgressBar from '../components/shared/ProgressBar.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const router = useRouter()
const gameTime = useGameTimeStore()
const notifications = useNotificationsStore()
const stats = ref<DashboardStats | null>(null)
const loading = ref(true)

// Expand state
const expandedPartyId = ref<number | null>(null)
const expandedBuilding = ref<string | null>(null)

// Drag state
const dragOverPartyId = ref<number | null>(null)
const dragOverBuilding = ref<string | null>(null)

async function fetchStats() {
  try {
    stats.value = await getDashboardStats()
  } finally {
    loading.value = false
  }
}

watch(() => gameTime.currentDay, fetchStats)
watch(() => gameTime.expeditionVersion, fetchStats)
onMounted(fetchStats)

function progressPct(exp: DashboardStats['active_expeditions'][0]): number {
  if (exp.duration_days <= 0) return 100
  return Math.min(100, Math.round((exp.days_elapsed / exp.duration_days) * 100))
}

function partyStatusClass(status: string): string {
  switch (status) {
    case 'Ready': return 'status-ready'
    case 'Healing': return 'status-healing'
    case 'On Expedition': return 'status-expedition'
    case 'Empty': return 'status-empty'
    default: return ''
  }
}

function toggleParty(id: number) {
  expandedPartyId.value = expandedPartyId.value === id ? null : id
}

function toggleBuilding(type: string) {
  expandedBuilding.value = expandedBuilding.value === type ? null : type
}

// Drag from unassigned
function onDragStart(e: DragEvent, advId: number) {
  e.dataTransfer?.setData('text/plain', String(advId))
  e.dataTransfer!.effectAllowed = 'move'
}

// Drop on party
function onPartyDragOver(e: DragEvent, partyId: number) {
  e.preventDefault()
  dragOverPartyId.value = partyId
}

function onPartyDragLeave() {
  dragOverPartyId.value = null
}

async function onPartyDrop(e: DragEvent, partyId: number) {
  e.preventDefault()
  dragOverPartyId.value = null
  const advId = Number(e.dataTransfer?.getData('text/plain'))
  if (!advId) return
  const adv = stats.value?.unassigned_adventurers.find(a => a.id === advId)
  const party = stats.value?.parties.find(p => p.id === partyId)
  try {
    await partiesApi.addMember({ party_id: partyId, adventurer_id: advId })
    notifications.add(`${adv?.name ?? 'Adventurer'} joined ${party?.name ?? 'party'}`, 'success')
    await fetchStats()
  } catch (err: any) {
    notifications.add(err?.data?.detail ?? 'Failed to add to party', 'error')
  }
}

// Drop on building
function onBuildingDragOver(e: DragEvent, buildingType: string) {
  e.preventDefault()
  dragOverBuilding.value = buildingType
}

function onBuildingDragLeave() {
  dragOverBuilding.value = null
}

async function onBuildingDrop(e: DragEvent, building: DashboardStats['buildings'][0]) {
  e.preventDefault()
  dragOverBuilding.value = null
  if (!building.id) return
  const advId = Number(e.dataTransfer?.getData('text/plain'))
  if (!advId) return
  const adv = stats.value?.unassigned_adventurers.find(a => a.id === advId)
  try {
    await buildingsApi.assign(building.id, advId)
    notifications.add(`${adv?.name ?? 'Adventurer'} assigned to ${building.name}`, 'success')
    await fetchStats()
  } catch (err: any) {
    notifications.add(err?.data?.detail ?? 'Failed to assign', 'error')
  }
}

// Auto-delve toggle
async function toggleAutoDelve(partyId: number, field: 'healed' | 'full') {
  const party = stats.value?.parties.find(p => p.id === partyId)
  if (!party) return
  const healed = field === 'healed' ? !party.auto_delve_healed : party.auto_delve_healed
  const full = field === 'full' ? !party.auto_delve_full : party.auto_delve_full
  try {
    await partiesApi.updateAutoDelve(partyId, healed, full)
    await fetchStats()
  } catch {
    notifications.add('Failed to update auto-delve', 'error')
  }
}
</script>

<template>
  <div>
    <LoadingSpinner v-if="loading" />
    <template v-else-if="stats">
      <!-- Dungeon header -->
      <div class="dungeon-header" v-if="stats.dungeon_name">
        <h1 class="dungeon-name">{{ stats.dungeon_name }}</h1>
        <span class="dungeon-depth">Depth {{ stats.max_dungeon_level }} reached</span>
      </div>
      <h1 v-else>Dashboard</h1>

      <!-- Hint -->
      <div v-if="stats.hint && stats.hint !== 'launch_expedition'" class="hint-bar mb-2">{{ stats.hint }}</div>

      <!-- Stat cards -->
      <div class="stat-row mb-2">
        <div class="stat-card clickable" @click="router.push('/adventurers')">
          <div class="stat-value">{{ stats.adventurer_count }}</div>
          <div class="stat-label">Adventurers</div>
        </div>
        <div class="stat-card clickable" @click="router.push('/parties')">
          <div class="stat-value">{{ stats.party_count }}</div>
          <div class="stat-label">Parties</div>
        </div>
        <div class="stat-card clickable" @click="router.push('/expeditions')">
          <div class="stat-value">{{ stats.expedition_count }}</div>
          <div class="stat-label">Expeditions</div>
        </div>
        <div class="stat-card clickable" @click="router.push('/village')">
          <div class="stat-value">{{ stats.buildings.length }}</div>
          <div class="stat-label">Buildings</div>
        </div>
      </div>

      <!-- Active Expeditions -->
      <div v-if="stats.active_expeditions.length > 0" class="card dash-card mb-2">
        <h3 class="mb-1">Active Expeditions</h3>
        <div class="active-list">
          <div
            v-for="exp in stats.active_expeditions"
            :key="exp.id"
            class="active-exp clickable"
            @click="router.push(`/expedition/${exp.id}/summary`)"
          >
            <div class="active-exp-info">
              <span class="active-exp-party">{{ exp.party_name }}</span>
              <span class="active-exp-meta">Depth {{ exp.dungeon_level }}</span>
              <span v-if="exp.result === 'awaiting_choice'" class="badge badge-warning">Decision</span>
            </div>
            <div class="active-exp-progress">
              <div class="progress-track">
                <div class="progress-fill" :style="{ width: progressPct(exp) + '%' }"></div>
              </div>
              <span class="active-exp-days">Day {{ exp.days_elapsed }}/{{ exp.duration_days }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Parties (expandable, drop target) -->
      <div class="card dash-card mb-2">
        <div class="flex flex-between mb-1">
          <h3>Parties</h3>
          <button class="btn btn-sm btn-primary" @click="router.push('/form-party')">+ New Party</button>
        </div>
        <div class="party-list">
          <div
            v-for="p in stats.parties"
            :key="p.id"
            class="party-block"
            :class="{ 'drop-hover': dragOverPartyId === p.id }"
            @dragover="onPartyDragOver($event, p.id)"
            @dragleave="onPartyDragLeave"
            @drop="onPartyDrop($event, p.id)"
          >
            <div class="party-row clickable" @click="toggleParty(p.id)">
              <span class="party-expand">{{ expandedPartyId === p.id ? '&#9660;' : '&#9654;' }}</span>
              <span class="party-name">{{ p.name }}</span>
              <span class="party-size">{{ p.member_count }}/6</span>
              <span class="badge" :class="partyStatusClass(p.status)">{{ p.status }}</span>
            </div>
            <div v-if="expandedPartyId === p.id" class="party-members">
              <div v-for="m in p.members" :key="m.id" class="party-member-row clickable" @click.stop="router.push(`/adventurers`)">
                <span class="member-name">{{ m.name }}</span>
                <span class="badge">{{ m.adventurer_class }}</span>
                <span class="stat">Lv {{ m.level }}</span>
                <span class="stat" :style="{ color: m.hp_current >= m.hp_max ? 'var(--accent-green)' : '#fbbf24' }">{{ m.hp_current }}/{{ m.hp_max }}</span>
                <span class="stat xp">{{ m.xp }}<template v-if="m.next_level_xp">/{{ m.next_level_xp }}</template> XP</span>
                <span class="stat gold">{{ formatCurrency(m.gold, m.silver, m.copper) }}</span>
              </div>
              <div v-if="p.members.length === 0" class="text-muted" style="font-size: 12px; padding: 4px 0">Drop adventurers here</div>
              <div class="party-actions">
                <button
                  v-if="p.status === 'On Expedition' && p.expedition_id"
                  class="btn btn-primary btn-sm"
                  @click.stop="router.push(`/expedition/${p.expedition_id}/summary`)"
                >View Expedition</button>
                <button
                  v-else-if="p.status === 'Ready'"
                  class="btn btn-primary btn-sm"
                  @click.stop="router.push(`/launch-expedition/${p.id}`)"
                >Launch Expedition</button>
                <button class="btn btn-sm btn-secondary" @click.stop="router.push(`/parties/${p.id}`)">Manage</button>
              </div>
              <div class="auto-delve-row">
                <span class="auto-delve-label">Auto-Delve:</span>
                <label class="checkbox-label" @click.stop>
                  <input type="checkbox" :checked="p.auto_delve_healed" @change="toggleAutoDelve(p.id, 'healed')" />
                  When Healed
                </label>
                <label class="checkbox-label" @click.stop>
                  <input type="checkbox" :checked="p.auto_delve_full" @change="toggleAutoDelve(p.id, 'full')" />
                  When Full
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Unassigned Adventurers (draggable) -->
      <div v-if="stats.unassigned_adventurers.length > 0" class="card dash-card mb-2">
        <h3 class="mb-1">Unassigned Adventurers</h3>
        <div class="unassigned-list">
          <div
            v-for="a in stats.unassigned_adventurers"
            :key="a.id"
            class="unassigned-row draggable"
            draggable="true"
            @dragstart="onDragStart($event, a.id)"
          >
            <span class="drag-handle">&#x2630;</span>
            <span class="unassigned-name">{{ a.name }}</span>
            <span class="badge">{{ a.adventurer_class }}</span>
            <span class="stat">Lv {{ a.level }}</span>
            <span class="stat" :style="{ color: a.hp_current >= a.hp_max ? 'var(--accent-green)' : '#fbbf24' }">{{ a.hp_current }}/{{ a.hp_max }}</span>
            <span class="stat xp">{{ a.xp }}<template v-if="a.next_level_xp">/{{ a.next_level_xp }}</template> XP</span>
            <span class="stat gold">{{ formatCurrency(a.gold, a.silver, a.copper) }}</span>
          </div>
        </div>
      </div>

      <!-- Village (expandable, drop target for buildings) -->
      <div v-if="stats.buildings.length > 0" class="card dash-card mb-2">
        <div class="flex flex-between mb-1">
          <h3>Village</h3>
          <button class="btn btn-sm btn-secondary" @click="router.push('/village')">Manage</button>
        </div>
        <div class="buildings-list">
          <div
            v-for="b in stats.buildings"
            :key="b.building_type"
            class="building-block"
            :class="{ 'drop-hover': dragOverBuilding === b.building_type }"
            @dragover="onBuildingDragOver($event, b.building_type)"
            @dragleave="onBuildingDragLeave"
            @drop="onBuildingDrop($event, b)"
          >
            <div class="building-row clickable" @click="toggleBuilding(b.building_type)">
              <span class="party-expand">{{ expandedBuilding === b.building_type ? '&#9660;' : '&#9654;' }}</span>
              <span class="building-row-name">{{ b.name }}</span>
              <span class="party-size">{{ b.assigned_count }} assigned</span>
              <span v-if="b.effects.length > 0" class="building-effect-tag">{{ b.effects[0] }}</span>
            </div>
            <div v-if="expandedBuilding === b.building_type" class="building-expanded">
              <div v-if="b.effects.length > 0" class="building-effects-full mb-1">
                <span v-for="(fx, i) in b.effects" :key="i" class="effect-tag">{{ fx }}</span>
              </div>
              <div v-if="b.assigned_adventurers.length > 0" class="building-assigned">
                <div v-for="a in b.assigned_adventurers" :key="a.id" class="building-assigned-row">
                  <span class="member-name">{{ a.name }}</span>
                  <span class="stat">Lv {{ a.level }}</span>
                </div>
              </div>
              <div v-else class="text-muted" style="font-size: 12px">Drop {{ b.adventurer_class }}s here to activate bonuses</div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="card dash-card mb-2 clickable" @click="router.push('/village')">
        <h3 class="mb-1">Village</h3>
        <p class="text-muted" style="font-size: 12px">No buildings yet. Visit the Village to build.</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dungeon-header { display: flex; align-items: baseline; gap: 12px; }
.dungeon-name { font-size: 1.3rem; }
.dungeon-depth { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); }

.hint-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; background: rgba(96, 165, 250, 0.08);
  border: 1px solid rgba(96, 165, 250, 0.2); border-radius: var(--border-radius);
  color: var(--accent-blue, #60a5fa); font-size: 13px;
}

.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; }

.stat-card {
  background: var(--bg-secondary); border: 1px solid var(--border-color);
  border-radius: var(--border-radius); padding: 10px 12px; text-align: center;
}
.stat-card.clickable { cursor: pointer; transition: border-color 0.15s; }
.stat-card.clickable:hover { border-color: var(--accent-green); }
.stat-value { font-family: var(--font-mono); font-size: 1.2rem; font-weight: 700; white-space: nowrap; }
.stat-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-top: 2px; }
.text-green { color: var(--accent-green); }

.dash-card { padding: 12px 16px; }

/* Active expeditions */
.active-list { display: flex; flex-direction: column; gap: 6px; }
.active-exp { display: flex; align-items: center; gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--border-color); }
.active-exp.clickable { cursor: pointer; }
.active-exp-info { display: flex; align-items: center; gap: 8px; min-width: 200px; }
.active-exp-party { font-weight: 600; font-size: 13px; }
.active-exp-meta { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }
.active-exp-progress { flex: 1; display: flex; align-items: center; gap: 8px; }
.progress-track { flex: 1; height: 6px; background: var(--bg-primary); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--accent-green); border-radius: 3px; transition: width 0.3s; }
.active-exp-days { font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); white-space: nowrap; }

/* Parties */
.party-list { display: flex; flex-direction: column; gap: 2px; }
.party-block { border-bottom: 1px solid var(--border-color); transition: background 0.15s; }
.party-block.drop-hover { background: rgba(74, 222, 128, 0.08); border-color: var(--accent-green); }
.party-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; cursor: pointer; }
.party-expand { font-size: 10px; color: var(--text-muted); width: 14px; }
.party-name { font-weight: 600; font-size: 13px; flex: 1; }
.party-size { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }

.party-members { padding: 4px 0 8px 22px; }
.party-member-row { display: flex; align-items: center; gap: 8px; padding: 3px 0; font-size: 12px; }
.member-name { font-weight: 600; flex: 1; font-size: 13px; }
.stat { font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); }
.party-actions { display: flex; gap: 6px; margin-top: 6px; }

.status-ready { background: rgba(74, 222, 128, 0.15); color: #4ade80; }
.status-healing { background: rgba(241, 196, 15, 0.15); color: #fbbf24; }
.status-expedition { background: rgba(96, 165, 250, 0.15); color: #60a5fa; }
.status-empty { background: rgba(128, 128, 128, 0.15); color: #888; }

/* Unassigned */
.unassigned-list { display: flex; flex-direction: column; gap: 3px; }
.unassigned-row {
  display: flex; align-items: center; gap: 8px;
  padding: 3px 0; border-bottom: 1px solid var(--border-color); font-size: 12px;
}
.unassigned-row.draggable { cursor: grab; }
.unassigned-row.draggable:active { cursor: grabbing; }
.drag-handle { color: var(--text-muted); font-size: 12px; }
.unassigned-name { font-weight: 600; flex: 1; font-size: 13px; }

/* Buildings */
.buildings-list { display: flex; flex-direction: column; gap: 2px; }
.building-block { border-bottom: 1px solid var(--border-color); transition: background 0.15s; }
.building-block.drop-hover { background: rgba(74, 222, 128, 0.08); border-color: var(--accent-green); }
.building-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; cursor: pointer; }
.building-row-name { font-weight: 600; font-size: 13px; flex: 1; }
.building-effect-tag { font-size: 10px; font-family: var(--font-mono); color: var(--accent-green); }
.building-expanded { padding: 4px 0 8px 22px; }
.building-effects-full { display: flex; gap: 6px; flex-wrap: wrap; }
.effect-tag {
  font-size: 11px; font-family: var(--font-mono); color: var(--accent-green);
  background: rgba(74, 222, 128, 0.08); padding: 2px 8px;
  border-radius: var(--border-radius); border: 1px solid rgba(74, 222, 128, 0.15);
}

.badge-warning { background: rgba(241, 196, 15, 0.15); color: #fbbf24; }

/* Auto-delve */
.auto-delve-row { display: flex; align-items: center; gap: 12px; padding: 6px 0; border-top: 1px solid var(--border-color); margin-top: 6px; }
.auto-delve-label { font-size: 12px; font-weight: 600; color: var(--text-muted); }
.checkbox-label { display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--text-secondary); cursor: pointer; }
.checkbox-label input[type="checkbox"] { accent-color: var(--accent-green); }

/* Enriched stats */
.stat.xp { color: var(--accent-blue, #60a5fa); }
.stat.gold { color: #fbbf24; }

/* Building assigned list */
.building-assigned { display: flex; flex-direction: column; gap: 2px; }
.building-assigned-row { display: flex; align-items: center; gap: 8px; padding: 2px 0; font-size: 12px; }
</style>
