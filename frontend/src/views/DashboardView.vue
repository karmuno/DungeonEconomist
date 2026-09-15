<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboardStats } from '../api/game'
import * as expeditionsApi from '../api/expeditions'
import * as partiesApi from '../api/parties'
import * as buildingsApi from '../api/buildings'
import * as adventurersApi from '../api/adventurers'
import type { DashboardStats, AdventurerOut } from '../types'
import { useGameTimeStore } from '../stores/gameTime'
import { useNotificationsStore, type NotificationType } from '../stores/notifications'
import { formatCurrency } from '../utils/currency'
import { itemEmoji, itemBonusLabel } from '../utils/adventurer'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import ModalDialog from '../components/shared/ModalDialog.vue'
import AdventurerDetail from '../components/adventurers/AdventurerDetail.vue'
import eventBus from '../eventBus'

const router = useRouter()
const gameTime = useGameTimeStore()
const notifications = useNotificationsStore()
const stats = ref<DashboardStats | null>(null)
const loading = ref(true)

// Adventurer detail modal
const selectedAdventurer = ref<AdventurerOut | null>(null)

async function openDetail(id: number) {
  selectedAdventurer.value = await adventurersApi.getById(id)
}

async function handleLevelUp() {
  if (!selectedAdventurer.value) return
  const result = await adventurersApi.levelUp(selectedAdventurer.value.id)
  notifications.add(`${selectedAdventurer.value.name} leveled up to ${result.new_level}! (+${result.hp_gained} HP)`, 'success')
  selectedAdventurer.value = await adventurersApi.getById(selectedAdventurer.value.id)
  await fetchStats()
}

// Expand state
const expandedPartyIds = ref<Set<number>>(new Set())
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

// Deliberately NOT watching gameTime.currentDay: the SidePanel emits
// 'refresh-dashboard' once the day's event popup is on screen, so state
// never updates ahead of its event being shown.
watch(() => gameTime.expeditionVersion, fetchStats)

function onDashboardData(data: DashboardStats) {
  stats.value = data
  loading.value = false
}

onMounted(() => {
  fetchStats()
  eventBus.on('refresh-dashboard', fetchStats)
  eventBus.on('dashboard-data', onDashboardData)
})

onUnmounted(() => {
  eventBus.off('refresh-dashboard', fetchStats)
  eventBus.off('dashboard-data', onDashboardData)
})

function progressPct(exp: DashboardStats['active_expeditions'][0]): number {
  if (exp.duration_days <= 0) return 100
  return Math.min(100, Math.round((exp.days_elapsed / exp.duration_days) * 100))
}

// Clicking the Decision badge re-opens the pending choice popup via the
// SidePanel's expedition-choice queue.
async function openDecision(expeditionId: number) {
  try {
    const pending = await expeditionsApi.getPending(expeditionId)
    if (!pending.pending_event) return
    eventBus.emit('game-events', [{
      type: 'expedition_choice',
      message: pending.pending_event.message,
      expedition_id: expeditionId,
      event_subtype: pending.pending_event.type,
    }])
  } catch {
    notifications.add('Failed to load the pending decision', 'error')
  }
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

type DashboardParty = DashboardStats['parties'][number]

// The status badge is the shortest path to whatever that party is doing:
// out delving -> its expedition, otherwise -> launch the next one.
function partyStatusRoute(p: DashboardParty): string | null {
  if (p.status === 'On Expedition') {
    return p.expedition_id ? `/expedition/${p.expedition_id}/summary` : null
  }
  return p.members.length > 0 ? `/launch-expedition/${p.id}` : null
}

function goToPartyStatus(p: DashboardParty) {
  const route = partyStatusRoute(p)
  if (route) router.push(route)
}

function toggleParty(id: number) {
  const next = new Set(expandedPartyIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  expandedPartyIds.value = next
}

function toggleBuilding(type: string) {
  expandedBuilding.value = expandedBuilding.value === type ? null : type
}

// A slot an adventurer can occupy: "unassigned", "party:ID", or "building:ID"
type Slot = string

const dragOverUnassigned = ref(false)
let dragSource: Slot = ''
let dragAdvId = 0
let dragAdvName = ''

type AdvEntry = DashboardStats['unassigned_adventurers'][number]

function onDragStart(e: DragEvent, advId: number, advName: string, source: Slot) {
  dragAdvId = advId
  dragAdvName = advName
  dragSource = source
  e.dataTransfer!.effectAllowed = 'move'
  e.dataTransfer?.setData('text/plain', String(advId))
}

function slotId(slot: Slot): number {
  return Number(slot.split(':')[1])
}

function findAndSpliceAdventurer(advId: number, slot: Slot): AdvEntry | null {
  if (!stats.value) return null
  if (slot === 'unassigned') {
    const idx = stats.value.unassigned_adventurers.findIndex(a => a.id === advId)
    if (idx === -1) return null
    return stats.value.unassigned_adventurers.splice(idx, 1)[0]
  }
  if (slot.startsWith('party:')) {
    const party = stats.value.parties.find(p => p.id === slotId(slot))
    if (!party) return null
    const idx = party.members.findIndex(m => m.id === advId)
    if (idx === -1) return null
    const adv = party.members.splice(idx, 1)[0]
    party.member_count = party.members.length
    return adv
  }
  if (slot.startsWith('building:')) {
    const building = stats.value.buildings.find(b => b.id === slotId(slot))
    if (!building) return null
    const idx = building.assigned_adventurers.findIndex(a => a.id === advId)
    if (idx === -1) return null
    const adv = building.assigned_adventurers.splice(idx, 1)[0]
    building.assigned_count = building.assigned_adventurers.length
    return adv
  }
  return null
}

// Local mirror of a server slot. False when the slot is gone from local state.
function insertLocal(slot: Slot, adv: AdvEntry): boolean {
  if (!stats.value) return false
  if (slot === 'unassigned') {
    stats.value.unassigned_adventurers.push(adv)
    return true
  }
  if (slot.startsWith('party:')) {
    const party = stats.value.parties.find(p => p.id === slotId(slot))
    if (!party) return false
    party.members.push(adv)
    party.member_count = party.members.length
    return true
  }
  if (slot.startsWith('building:')) {
    const building = stats.value.buildings.find(b => b.id === slotId(slot))
    if (!building) return false
    building.assigned_adventurers.push(adv)
    building.assigned_count = building.assigned_adventurers.length
    return true
  }
  return false
}

// Server call that vacates a slot. "unassigned" needs none.
function vacateSlotApi(slot: Slot, advId: number): Promise<unknown> | undefined {
  if (slot.startsWith('party:')) {
    return partiesApi.removeMember({ party_id: slotId(slot), adventurer_id: advId })
  }
  if (slot.startsWith('building:')) {
    return buildingsApi.unassign(slotId(slot), advId)
  }
}

// Server call that fills a slot. "unassigned" needs none: vacating the
// source already leaves the adventurer there.
function fillSlotApi(slot: Slot, advId: number): Promise<unknown> | undefined {
  if (slot.startsWith('party:')) {
    return partiesApi.addMember({ party_id: slotId(slot), adventurer_id: advId })
  }
  if (slot.startsWith('building:')) {
    return buildingsApi.assign(slotId(slot), advId)
  }
}

function errorDetail(err: unknown, fallback: string): string {
  return (err as { data?: { detail?: string } } | null)?.data?.detail ?? fallback
}

/**
 * Move an adventurer between slots, showing the move immediately.
 *
 * On failure they go back to their original slot. Only if the original slot
 * refuses them (e.g. the party disbanded the moment they left it) do they
 * land in Unassigned. Server truth is re-fetched afterwards either way.
 */
async function moveAdventurer(
  advId: number,
  advName: string,
  source: Slot,
  dest: Slot,
  successMsg: string,
  successType: NotificationType,
  failMsg: string,
) {
  if (!stats.value || source === dest) return
  const adv = findAndSpliceAdventurer(advId, source)
  if (!adv) return
  if (!insertLocal(dest, adv)) {
    insertLocal(source, adv)
    return
  }
  const successNoteId = notifications.add(successMsg, successType)

  // Vacating the last seat disbands the party, so there is no slot to return to
  let sourceGone: boolean
  try {
    const vacated = await vacateSlotApi(source, advId)
    sourceGone = Boolean((vacated as { deleted?: boolean } | undefined)?.deleted)
  } catch (err) {
    // Nothing changed on the server: the original slot still holds them
    if (successNoteId !== undefined) notifications.remove(successNoteId)
    notifications.add(errorDetail(err, failMsg), 'error')
    findAndSpliceAdventurer(advId, dest)
    insertLocal(source, adv)
    fetchStats()
    return
  }

  try {
    await fillSlotApi(dest, advId)
  } catch (err) {
    if (successNoteId !== undefined) notifications.remove(successNoteId)
    notifications.add(errorDetail(err, failMsg), 'error')
    findAndSpliceAdventurer(advId, dest)
    let restored = source === 'unassigned'
    if (!restored && !sourceGone) {
      try {
        await fillSlotApi(source, advId)
        restored = true
      } catch {
        // Original slot refused them; they stay unassigned on the server
      }
    }
    if (!restored || !insertLocal(source, adv)) {
      insertLocal('unassigned', adv)
      notifications.add(`${advName} returned to tavern`, 'info')
    }
  }
  fetchStats()
}

// Drop on party
function onPartyDragOver(e: DragEvent, partyId: number) {
  e.preventDefault()
  dragOverPartyId.value = partyId
}
function onPartyDragLeave() { dragOverPartyId.value = null }

async function onPartyDrop(e: DragEvent, partyId: number) {
  e.preventDefault()
  dragOverPartyId.value = null
  if (!dragAdvId) return
  const party = stats.value?.parties.find(p => p.id === partyId)
  if (!party) return
  await moveAdventurer(
    dragAdvId, dragAdvName, dragSource, `party:${partyId}`,
    `${dragAdvName} joined ${party.name}`, 'success', 'Failed to add to party',
  )
}

// Drop on building
function onBuildingDragOver(e: DragEvent, buildingType: string) {
  e.preventDefault()
  dragOverBuilding.value = buildingType
}
function onBuildingDragLeave() { dragOverBuilding.value = null }

async function onBuildingDrop(e: DragEvent, building: DashboardStats['buildings'][0]) {
  e.preventDefault()
  dragOverBuilding.value = null
  if (!building.id || !dragAdvId) return
  await moveAdventurer(
    dragAdvId, dragAdvName, dragSource, `building:${building.id}`,
    `${dragAdvName} assigned to ${building.name}`, 'success', 'Failed to assign',
  )
}

// Drop on unassigned zone (to unassign from party or building)
function onUnassignedDragOver(e: DragEvent) {
  if (dragSource !== 'unassigned') {
    e.preventDefault()
    dragOverUnassigned.value = true
  }
}
function onUnassignedDragLeave() { dragOverUnassigned.value = false }

async function onUnassignedDrop(e: DragEvent) {
  e.preventDefault()
  dragOverUnassigned.value = false
  if (!dragAdvId) return
  await moveAdventurer(
    dragAdvId, dragAdvName, dragSource, 'unassigned',
    `${dragAdvName} returned to tavern`, 'info', 'Failed to unassign',
  )
}

// Direct unassign buttons
async function removeFromParty(partyId: number, advId: number, advName: string) {
  await moveAdventurer(
    advId, advName, `party:${partyId}`, 'unassigned',
    `${advName} removed from party`, 'info', 'Failed to remove',
  )
}

async function unassignFromBuilding(buildingId: number, advId: number, advName: string) {
  await moveAdventurer(
    advId, advName, `building:${buildingId}`, 'unassigned',
    `${advName} returned to tavern`, 'info', 'Failed to unassign',
  )
}

// Auto-delve / auto-decide toggle
// One checkbox drives both auto-delve flags (kept separate in the backend)
async function togglePartySetting(partyId: number, field: 'auto_delve' | 'auto_decide') {
  const party = stats.value?.parties.find(p => p.id === partyId)
  if (!party) return
  const autoDelveOn = party.auto_delve_healed || party.auto_delve_full
  const auto = field === 'auto_delve' ? !autoDelveOn : autoDelveOn
  const autoDecide = field === 'auto_decide' ? !party.auto_decide_events : party.auto_decide_events
  try {
    await partiesApi.updateAutoDelve(partyId, auto, auto, autoDecide, party.auto_delve_level)
    await fetchStats()
  } catch {
    notifications.add('Failed to update settings', 'error')
  }
}

function avgPartyLevel(members: Array<{ level: number }>): string {
  if (members.length === 0) return '—'
  const sum = members.reduce((acc, m) => acc + m.level, 0)
  return (sum / 6).toFixed(1)
}

async function setAutoDelveLevel(partyId: number, level: number | null) {
  const party = stats.value?.parties.find(p => p.id === partyId)
  if (!party) return
  try {
    await partiesApi.updateAutoDelve(partyId, party.auto_delve_healed, party.auto_delve_full, party.auto_decide_events, level)
    await fetchStats()
  } catch {
    notifications.add('Failed to update settings', 'error')
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
              <span
                v-if="exp.result === 'awaiting_choice'"
                class="badge badge-warning decision-badge"
                title="Open the pending decision"
                @click.stop="openDecision(exp.id)"
              >Decision</span>
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

      <!-- Two column stacks. Left: Unassigned with the Village directly beneath, so a
           building assignment is a drag between neighbours, never a drag while scrolling.
           Right: Parties. Independent stacks rather than one grid, so a tall Parties card
           never opens a gap above the Village. -->
      <div class="parties-unassigned-grid mb-2">
      <div class="dash-column">

      <!-- Unassigned Adventurers -->
      <div
        class="card dash-card"
        :class="{ 'drop-hover': dragOverUnassigned }"
        @dragover="onUnassignedDragOver"
        @dragleave="onUnassignedDragLeave"
        @drop="onUnassignedDrop"
      >
        <h3 class="mb-1">Unassigned Adventurers</h3>
        <div v-if="stats.unassigned_adventurers.length === 0" class="text-muted" style="font-size: 12px">
          Drag adventurers here to unassign them
        </div>
        <div class="unassigned-list no-remove" :class="{ 'no-items': !stats.unassigned_adventurers.some(a => a.magic_items.length) }">
          <div
            v-for="a in stats.unassigned_adventurers"
            :key="a.id"
            class="unassigned-row adv-grid draggable"
            draggable="true"
            @dragstart="onDragStart($event, a.id, a.name, 'unassigned')"
            @click.stop="openDetail(a.id)"
          >
            <span class="drag-handle">&#x2630;</span>
            <span class="unassigned-name" :title="a.name">{{ a.name }}</span>
            <span class="row-items"><span v-for="item in a.magic_items" :key="item.id" class="item-tag" :title="item.name">{{ itemEmoji(item.item_type) }}{{ itemBonusLabel(item.item_type, item.bonus) }}</span></span>
            <span class="badge">{{ a.adventurer_class }}</span>
            <span class="stat">Lv {{ a.level }}</span>
            <span class="stat" :style="{ color: a.hp_current >= a.hp_max ? 'var(--accent-green)' : '#fbbf24' }">{{ a.hp_current }}/{{ a.hp_max }}</span>
            <span class="stat xp">{{ a.xp }}<template v-if="a.next_level_xp">/{{ a.next_level_xp }}</template> XP</span>
            <span class="stat gold">{{ formatCurrency(a.gold, a.silver, a.copper) }}</span>
          </div>
        </div>
      </div>

        <!-- Village (expandable, drop target for buildings) -->
        <div v-if="stats.buildings.length > 0" class="card dash-card">
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
                <span class="building-cell">
                  <span v-for="(fx, i) in b.staffed_effects" :key="i" class="building-effect-tag">{{ fx }}</span>
                </span>
                <span class="building-cell">
                  <span v-for="(fx, i) in b.standing_effects" :key="i" class="building-effect-tag">{{ fx }}</span>
                </span>
              </div>
              <div v-if="expandedBuilding === b.building_type" class="building-expanded">
                <div v-if="b.effects.length > 0" class="building-effects-full mb-1">
                  <span v-for="(fx, i) in b.effects" :key="i" class="effect-tag">{{ fx }}</span>
                </div>
                <div
                  v-if="b.assigned_adventurers.length > 0"
                  class="building-assigned"
                  :class="{ 'no-items': !b.assigned_adventurers.some(a => a.magic_items.length) }"
                >
                  <div
                    v-for="a in b.assigned_adventurers"
                    :key="a.id"
                    class="building-assigned-row adv-grid draggable"
                    draggable="true"
                    @dragstart="onDragStart($event, a.id, a.name, `building:${b.id}`)"
                    @click.stop="openDetail(a.id)"
                  >
                    <span class="drag-handle">&#x2630;</span>
                    <span class="member-name" :title="a.name">{{ a.name }}</span>
                    <span class="row-items"><span v-for="item in a.magic_items" :key="item.id" class="item-tag" :title="item.name">{{ itemEmoji(item.item_type) }}{{ itemBonusLabel(item.item_type, item.bonus) }}</span></span>
                    <span class="badge">{{ a.adventurer_class }}</span>
                    <span class="stat">Lv {{ a.level }}</span>
                    <span class="stat" :style="{ color: a.hp_current >= a.hp_max ? 'var(--accent-green)' : '#fbbf24' }">{{ a.hp_current }}/{{ a.hp_max }}</span>
                    <span class="stat xp">{{ a.xp }}<template v-if="a.next_level_xp">/{{ a.next_level_xp }}</template> XP</span>
                    <span class="stat gold">{{ formatCurrency(a.gold, a.silver, a.copper) }}</span>
                    <button class="remove-btn" @click.stop="unassignFromBuilding(b.id, a.id, a.name)">&times;</button>
                  </div>
                </div>
                <div v-else class="text-muted" style="font-size: 12px">Drop {{ b.adventurer_class }}s here to activate bonuses</div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="card dash-card clickable" @click="router.push('/village')">
          <h3 class="mb-1">Village</h3>
          <p class="text-muted" style="font-size: 12px">No buildings yet. Visit the Village to build.</p>
        </div>

      </div> <!-- end left column -->
      <div class="dash-column">

      <!-- Parties (expandable, drop target) -->
      <div class="card dash-card">
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
              <span class="party-expand">{{ expandedPartyIds.has(p.id) ? '&#9660;' : '&#9654;' }}</span>
              <span class="party-name">{{ p.name }}</span>
              <span class="party-size">{{ p.member_count }}/6</span>
              <span class="party-avg-level">avg Lv {{ avgPartyLevel(p.members) }}</span>
              <span
                class="badge"
                :class="[partyStatusClass(p.status), { 'status-link': partyStatusRoute(p) }]"
                :title="p.status === 'On Expedition' ? 'View expedition' : partyStatusRoute(p) ? 'Launch expedition' : undefined"
                @click.stop="goToPartyStatus(p)"
              >{{ p.status }}</span>
            </div>
            <div
              v-if="expandedPartyIds.has(p.id)"
              class="party-members"
              :class="{ 'no-items': !p.members.some(m => m.magic_items.length), 'no-remove': p.on_expedition }"
            >
              <div
                v-for="m in p.members"
                :key="m.id"
                class="party-member-row adv-grid draggable"
                draggable="true"
                @dragstart="onDragStart($event, m.id, m.name, `party:${p.id}`)"
                @click.stop="openDetail(m.id)"
              >
                <span class="drag-handle">&#x2630;</span>
                <span :class="['member-name', { 'text-dead': m.hp_current <= 0 }]" :title="m.name">{{ m.name }}</span>
                <span class="row-items"><span v-for="item in m.magic_items" :key="item.id" class="item-tag" :title="item.name">{{ itemEmoji(item.item_type) }}{{ itemBonusLabel(item.item_type, item.bonus) }}</span></span>
                <span class="badge">{{ m.adventurer_class }}</span>
                <span class="stat">Lv {{ m.level }}</span>
                <span class="stat" :style="{ color: m.hp_current >= m.hp_max ? 'var(--accent-green)' : '#fbbf24' }">{{ m.hp_current }}/{{ m.hp_max }}</span>
                <span class="stat xp">{{ m.xp }}<template v-if="m.next_level_xp">/{{ m.next_level_xp }}</template> XP</span>
                <span class="stat gold">{{ formatCurrency(m.gold, m.silver, m.copper) }}</span>
                <button v-if="!p.on_expedition" class="remove-btn" @click.stop="removeFromParty(p.id, m.id, m.name)">&times;</button>
              </div>
              <div v-if="p.members.length === 0" class="text-muted" style="font-size: 12px; padding: 4px 0">Drop adventurers here</div>
              <div class="party-actions">
                <button
                  v-if="p.status === 'On Expedition' && p.expedition_id"
                  class="btn btn-primary btn-sm"
                  @click.stop="router.push(`/expedition/${p.expedition_id}/summary`)"
                >View Expedition</button>
                <button
                  v-if="p.status !== 'On Expedition' && p.members.length > 0"
                  class="btn btn-primary btn-sm"
                  @click.stop="router.push(`/launch-expedition/${p.id}`)"
                >Launch Expedition</button>
                <button class="btn btn-sm btn-secondary" @click.stop="router.push(`/parties/${p.id}`)">Manage</button>
              </div>
              <div class="auto-delve-row">
                <label class="checkbox-label" title="Party will automatically start an expedition when it has 6 fully-healed members." @click.stop>
                  <input type="checkbox" :checked="p.auto_delve_healed || p.auto_delve_full" @change="togglePartySetting(p.id, 'auto_delve')" />
                  Auto-Delve
                </label>
                <select
                  class="form-select auto-level-select"
                  :value="p.auto_delve_level ?? 1"
                  @click.stop
                  @change="setAutoDelveLevel(p.id, Number(($event.target as HTMLSelectElement).value) || 1)"
                >
                  <option v-for="n in (stats?.max_dungeon_level ?? 1)" :key="n" :value="n">Depth {{ n }}</option>
                </select>
                <span class="auto-delve-label" style="margin-left: 8px">|</span>
                <label class="checkbox-label" @click.stop>
                  <input type="checkbox" :checked="p.auto_decide_events" @change="togglePartySetting(p.id, 'auto_decide')" />
                  Auto-Decide Events
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      </div> <!-- end right column -->
      </div> <!-- end parties-unassigned-grid -->

    </template>
  </div>

  <!-- Adventurer detail modal -->
  <ModalDialog
    :is-open="!!selectedAdventurer"
    :title="selectedAdventurer?.name ?? ''"
    @close="selectedAdventurer = null"
  >
    <AdventurerDetail
      v-if="selectedAdventurer"
      :adventurer="selectedAdventurer"
      @close="selectedAdventurer = null"
      @level-up="handleLevelUp"
    />
  </ModalDialog>
</template>

<style scoped>
.dungeon-header { display: flex; align-items: baseline; gap: 12px; }
.dungeon-name { font-size: 1.3rem; }
.dungeon-depth { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); }

.text-green { color: var(--accent-green); }
.text-dead { color: var(--accent-red, #e74c3c); }

.dash-card { padding: 12px 16px; }
.parties-unassigned-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}
.dash-column { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
/* Below this the two stacks cannot each hold a full adventurer row; stack them */
@media (max-width: 1280px) {
  .parties-unassigned-grid { grid-template-columns: minmax(0, 1fr); }
}

/* One grid per adventurer row with fixed tracks, so every statistic sits in the
   same column from one adventurer to the next, whatever they carry:
   handle | name | items | class | level | HP | XP | wealth | remove
   A list whose rows carry no items, or no remove button, collapses that track so
   the name gets the room; alignment only has to hold within one list. */
.adv-grid {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr) var(--items-col, 36px) 86px 36px 48px minmax(60px, max-content) minmax(44px, max-content) var(--remove-col, 18px);
  column-gap: 6px;
  align-items: center;
}
.adv-grid .stat { white-space: nowrap; text-align: right; }
.adv-grid .badge { justify-self: start; }
.adv-grid .remove-btn { justify-self: end; }
/* Fixed-width item cell; four or more items is rare enough that wrapping onto a
   second line is the accepted degrading case */
.row-items { display: flex; flex-wrap: wrap; gap: 2px; min-width: 0; }
.no-items { --items-col: 0px; }
.no-remove { --remove-col: 0px; }

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
/* Fixed tracks so the status badge never pushes size and level around:
   caret | name | size | average level | status */
.party-row {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr) 36px 72px 104px;
  column-gap: 8px;
  align-items: center;
  padding: 6px 0;
  cursor: pointer;
  font-size: 12px;
}
.party-expand { font-size: 10px; color: var(--text-muted); }
.party-name { font-weight: 600; font-size: 13px; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.party-size { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); white-space: nowrap; text-align: right; }
.party-avg-level { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); white-space: nowrap; text-align: right; }
.party-row .badge { justify-self: end; }

.party-members { padding: 4px 0 8px 22px; }
.party-member-row { padding: 3px 0; font-size: 12px; cursor: pointer; }
.member-name { font-weight: 600; font-size: 12px; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stat { font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); }
.party-actions { display: flex; gap: 6px; margin-top: 6px; }

.status-ready { background: rgba(74, 222, 128, 0.15); color: #4ade80; }
.status-healing { background: rgba(241, 196, 15, 0.15); color: #fbbf24; }
.status-expedition { background: rgba(96, 165, 250, 0.15); color: #60a5fa; }
.status-empty { background: rgba(128, 128, 128, 0.15); color: #888; }

/* A status that goes somewhere: dotted underline, brightening on hover */
.status-link {
  cursor: pointer;
  text-decoration: underline;
  text-decoration-style: dotted;
  text-decoration-color: currentColor;
  text-underline-offset: 2px;
}
.status-link:hover {
  text-decoration-style: solid;
  filter: brightness(1.25);
}

/* Unassigned */
.unassigned-list { display: flex; flex-direction: column; gap: 3px; }
.unassigned-row {
  padding: 3px 0; border-bottom: 1px solid var(--border-color); font-size: 12px;
  cursor: pointer;
}
.unassigned-row.draggable { cursor: pointer; }
.unassigned-row.draggable:active { cursor: pointer; }
.drag-handle { color: var(--text-muted); font-size: 12px; }
.unassigned-name { font-weight: 600; font-size: 12px; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Buildings */
.buildings-list { display: flex; flex-direction: column; gap: 2px; }
.building-block { border-bottom: 1px solid var(--border-color); transition: background 0.15s; }
.building-block.drop-hover { background: rgba(74, 222, 128, 0.08); border-color: var(--accent-green); }
/* One grid per row with fixed tracks, so every row's cells line up as a table:
   caret | name | assigned | what the staff deliver | what the building grants */
.building-row {
  display: grid;
  grid-template-columns: 14px minmax(120px, 1fr) 84px minmax(0, 2fr) minmax(0, 2fr);
  align-items: center;
  column-gap: 8px;
  padding: 6px 0;
  cursor: pointer;
}
.building-row-name { font-weight: 600; font-size: 13px; }
.building-cell { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.building-effect-tag { font-size: 10px; font-family: var(--font-mono); color: var(--accent-green); }
.building-effect-tag + .building-effect-tag::before { content: '\B7'; margin-right: 8px; color: var(--text-muted); }
.building-expanded { padding: 4px 0 8px 22px; }
.building-effects-full { display: flex; gap: 6px; flex-wrap: wrap; }
.effect-tag {
  font-size: 11px; font-family: var(--font-mono); color: var(--accent-green);
  background: rgba(74, 222, 128, 0.08); padding: 2px 8px;
  border-radius: var(--border-radius); border: 1px solid rgba(74, 222, 128, 0.15);
}

.badge-warning { background: rgba(241, 196, 15, 0.15); color: #fbbf24; }
.decision-badge { cursor: pointer; }
.decision-badge:hover { background: rgba(241, 196, 15, 0.3); }

/* Auto-delve */
.auto-delve-row { display: flex; align-items: center; gap: 12px; padding: 6px 0; border-top: 1px solid var(--border-color); margin-top: 6px; }
.auto-delve-label { font-size: 12px; font-weight: 600; color: var(--text-muted); }
.checkbox-label { display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--text-secondary); cursor: pointer; }
.checkbox-label input[type="checkbox"] { accent-color: var(--accent-green); }
.auto-level-select { width: auto; min-width: 90px; padding: 2px 6px; font-size: 11px; }

/* Enriched stats */
.stat.xp { color: var(--accent-blue, #60a5fa); }
.stat.gold { color: #fbbf24; }

/* Building assigned list */
.building-assigned { display: flex; flex-direction: column; gap: 2px; }
.building-assigned-row { padding: 2px 0; font-size: 12px; cursor: pointer; }

/* Remove/drag controls */
.remove-btn {
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  font-size: 16px; padding: 0 2px; line-height: 1; opacity: 0.5; flex-shrink: 0;
}
.remove-btn:hover { color: var(--accent-red, #e74c3c); opacity: 1; }
.draggable { cursor: grab; }
.draggable:active { cursor: grabbing; }
.party-member-row.draggable,
.building-assigned-row.draggable { cursor: pointer; }
.party-member-row.draggable:active,
.building-assigned-row.draggable:active { cursor: pointer; }
.drop-hover { background: rgba(74, 222, 128, 0.08) !important; border-color: var(--accent-green) !important; }

.item-tag {
  font-size: 11px; font-family: var(--font-mono); color: #fbbf24;
  background: rgba(251, 191, 36, 0.1); padding: 1px 4px;
  border-radius: 3px; white-space: nowrap;
}
</style>
