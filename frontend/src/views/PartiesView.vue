<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { AdventurerOut, PartyOut, ExpeditionSummary } from '../types'
import * as adventurersApi from '../api/adventurers'
import * as partiesApi from '../api/parties'
import * as expeditionsApi from '../api/expeditions'
import * as gameApi from '../api/game'
import { useNotificationsStore } from '../stores/notifications'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import AdventurerLink from '../components/adventurers/AdventurerLink.vue'

const router = useRouter()
const route = useRoute()
const notifications = useNotificationsStore()

const allAdventurers = ref<AdventurerOut[]>([])
const parties = ref<PartyOut[]>([])
const selectedPartyId = ref<number | null>(null)
const classFilter = ref('')
const loading = ref(true)
const confirmingDisband = ref(false)

const MAX_PARTY_SIZE = 6

const selectedParty = computed(() =>
  parties.value.find((p) => p.id === selectedPartyId.value) ?? null
)

// IDs of adventurers in ANY party
const allPartyMemberIds = computed(() => {
  const ids = new Set<number>()
  for (const p of parties.value) {
    for (const m of p.members) {
      ids.add(m.id)
    }
  }
  return ids
})

const availableAdventurers = computed(() => {
  return allAdventurers.value.filter((a) => {
    if (allPartyMemberIds.value.has(a.id)) return false
    if (!a.is_available || a.on_expedition || a.is_dead || a.is_bankrupt) return false
    if (classFilter.value && a.adventurer_class !== classFilter.value) return false
    return true
  })
})

onMounted(async () => {
  await fetchAll()
  loading.value = false
})

const expeditions = ref<ExpeditionSummary[]>([])
const maxDungeonLevel = ref(1)

// Current expedition for the selected party (if on expedition)
const currentExpedition = computed(() => {
  if (!selectedParty.value?.on_expedition) return null
  return expeditions.value.find(e =>
    e.party_id === selectedParty.value!.id && (e.result === 'in_progress' || e.result === 'awaiting_choice')
  ) ?? null
})

async function fetchAll() {
  allAdventurers.value = await adventurersApi.list()
  parties.value = await partiesApi.list()
  expeditions.value = await expeditionsApi.list()
  try {
    const dungeon = await gameApi.getDungeonInfo()
    maxDungeonLevel.value = dungeon.max_dungeon_level
  } catch { /* keep default */ }
  // Select from route param, or first party
  const paramId = Number(route.params.partyId)
  if (paramId && parties.value.some(p => p.id === paramId)) {
    selectedPartyId.value = paramId
  } else if (selectedPartyId.value === null && parties.value.length > 0) {
    selectedPartyId.value = parties.value[0].id
  }
}

// Reset disband confirmation when switching parties
watch(selectedPartyId, () => {
  confirmingDisband.value = false
})

function hpColor(adv: AdventurerOut): string {
  const pct = adv.hp_max > 0 ? adv.hp_current / adv.hp_max : 0
  if (pct >= 0.6) return 'var(--accent-green)'
  if (pct >= 0.3) return '#fbbf24'
  return 'var(--accent-red, #e74c3c)'
}

async function addMember(adv: AdventurerOut) {
  if (!selectedParty.value || selectedParty.value.members.length >= MAX_PARTY_SIZE) return
  if (selectedParty.value.on_expedition) return
  try {
    await partiesApi.addMember({ party_id: selectedParty.value.id, adventurer_id: adv.id })
    await fetchAll()
  } catch {
    notifications.add('Failed to add member', 'error')
  }
}

async function removeMember(id: number) {
  if (!selectedParty.value) return
  if (selectedParty.value.on_expedition) return

  // Last member — confirm disband
  if (selectedParty.value.members.length <= 1) {
    if (!confirmingDisband.value) {
      confirmingDisband.value = true
      return
    }
    try {
      const name = selectedParty.value.name
      await partiesApi.deleteParty(selectedParty.value.id)
      selectedPartyId.value = null
      confirmingDisband.value = false
      notifications.add(`Party "${name}" disbanded`, 'info')
      await fetchAll()
    } catch {
      notifications.add('Failed to disband party', 'error')
      confirmingDisband.value = false
    }
    return
  }

  try {
    await partiesApi.removeMember({ party_id: selectedParty.value.id, adventurer_id: id })
    await fetchAll()
  } catch {
    notifications.add('Failed to remove member', 'error')
  }
}

async function togglePartySetting(field: 'healed' | 'full' | 'auto_decide') {
  if (!selectedParty.value) return
  const healed = field === 'healed' ? !selectedParty.value.auto_delve_healed : selectedParty.value.auto_delve_healed
  const full = field === 'full' ? !selectedParty.value.auto_delve_full : selectedParty.value.auto_delve_full
  const autoDecide = field === 'auto_decide' ? !selectedParty.value.auto_decide_events : selectedParty.value.auto_decide_events
  try {
    await partiesApi.updateAutoDelve(selectedParty.value.id, healed, full, autoDecide, selectedParty.value.auto_delve_level)
    await fetchAll()
  } catch {
    notifications.add('Failed to update settings', 'error')
  }
}

async function setAutoDelveLevel(level: number | null) {
  if (!selectedParty.value) return
  try {
    await partiesApi.updateAutoDelve(
      selectedParty.value.id,
      selectedParty.value.auto_delve_healed,
      selectedParty.value.auto_delve_full,
      selectedParty.value.auto_decide_events,
      level,
    )
    await fetchAll()
  } catch {
    notifications.add('Failed to update settings', 'error')
  }
}

async function deleteParty() {
  if (!selectedParty.value) return
  if (!confirmingDisband.value) {
    confirmingDisband.value = true
    return
  }
  try {
    const name = selectedParty.value.name
    await partiesApi.deleteParty(selectedParty.value.id)
    selectedPartyId.value = null
    confirmingDisband.value = false
    notifications.add(`Party "${name}" disbanded`, 'info')
    await fetchAll()
  } catch {
    notifications.add('Failed to disband party', 'error')
    confirmingDisband.value = false
  }
}
</script>

<template>
  <div>
    <div class="flex flex-between mb-3">
      <h1>Manage Parties</h1>
      <button class="btn btn-primary" @click="router.push('/form-party')">
        Form New Party
      </button>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else-if="parties.length === 0" class="text-muted">
      No parties yet. <a href="#" @click.prevent="router.push('/form-party')">Form one</a> to get started.
    </div>
    <div v-else class="formation-layout">
      <!-- Left: Available Adventurers -->
      <div class="formation-column card">
        <h3 class="mb-2">Available Adventurers</h3>
        <div class="filters-bar mb-2">
          <select v-model="classFilter" class="form-select">
            <option value="">All Classes</option>
            <option v-for="cls in ['Fighter', 'Cleric', 'Magic-User', 'Elf', 'Dwarf', 'Halfling']" :key="cls" :value="cls">
              {{ cls }}
            </option>
          </select>
        </div>
        <div v-if="!selectedParty" class="text-muted">Select a party on the right</div>
        <div v-else-if="selectedParty.on_expedition" class="text-muted">Party is on expedition</div>
        <template v-else>
          <div v-if="availableAdventurers.length === 0" class="text-muted">No available adventurers</div>
          <div
            v-for="adv in availableAdventurers"
            :key="adv.id"
            class="adv-row"
          >
            <div class="adv-main">
              <AdventurerLink :name="adv.name" class="adv-name" />
              <span class="badge">{{ adv.adventurer_class }}</span>
            </div>
            <div class="adv-stats">
              <span class="stat">Lv {{ adv.level }}</span>
              <span class="stat" :style="{ color: hpColor(adv) }">{{ adv.hp_current }}/{{ adv.hp_max }} HP</span>
              <span class="stat xp">{{ adv.xp }}<template v-if="adv.next_level_xp"> / {{ adv.next_level_xp }}</template> XP</span>
            </div>
            <button
              class="btn btn-primary btn-sm"
              :disabled="!selectedParty || selectedParty.members.length >= MAX_PARTY_SIZE"
              @click="addMember(adv)"
            >
              +
            </button>
          </div>
        </template>
      </div>

      <!-- Right: Party Members -->
      <div class="formation-column card">
        <h3 class="mb-2">Party Members
          <template v-if="selectedParty">({{ selectedParty.members.length }}/{{ MAX_PARTY_SIZE }})</template>
        </h3>
        <div class="form-group mb-2">
          <select v-model="selectedPartyId" class="form-select">
            <option :value="null" disabled>Select a party...</option>
            <option
              v-for="p in parties"
              :key="p.id"
              :value="p.id"
            >
              {{ p.name }} ({{ p.members.length }}/{{ MAX_PARTY_SIZE }})
            </option>
          </select>
        </div>
        <template v-if="selectedParty">
          <div v-if="selectedParty.members.length === 0" class="text-muted">No members</div>
          <div
            v-for="member in selectedParty.members"
            :key="member.id"
            class="adv-row"
          >
            <div class="adv-main">
              <AdventurerLink :name="member.name" class="adv-name" />
              <span class="badge">{{ member.adventurer_class }}</span>
            </div>
            <div class="adv-stats">
              <span class="stat">Lv {{ member.level }}</span>
              <span class="stat" :style="{ color: hpColor(member) }">{{ member.hp_current }}/{{ member.hp_max }} HP</span>
              <span class="stat xp">{{ member.xp }} XP</span>
            </div>
            <button
              class="btn btn-danger btn-sm"
              :disabled="selectedParty.on_expedition"
              @click="removeMember(member.id)"
            >
              {{ confirmingDisband && selectedParty.members.length <= 1 ? '?' : '×' }}
            </button>
          </div>
          <div class="mt-3 flex gap-1">
            <button
              v-if="currentExpedition"
              class="btn btn-primary btn-sm"
              @click="router.push(`/expedition/${currentExpedition.id}/summary`)"
            >
              View Current Expedition
            </button>
            <button
              v-else
              class="btn btn-primary btn-sm"
              :disabled="selectedParty.on_expedition || selectedParty.members.length === 0"
              @click="router.push(`/launch-expedition/${selectedParty.id}`)"
            >
              Launch Expedition
            </button>
            <button
              class="btn btn-danger btn-sm"
              :disabled="selectedParty.on_expedition"
              @click="deleteParty"
            >
              {{ confirmingDisband ? 'Are you sure? This will disband the party.' : 'Disband Party' }}
            </button>
          </div>
          <div class="auto-delve-row mt-2">
            <span class="auto-delve-label">Auto-Delve:</span>
            <label class="checkbox-label">
              <input
                type="checkbox"
                :checked="selectedParty.auto_delve_healed"
                @change="togglePartySetting('healed')"
              />
              When Healed
            </label>
            <label class="checkbox-label">
              <input
                type="checkbox"
                :checked="selectedParty.auto_delve_full"
                @change="togglePartySetting('full')"
              />
              When Full
            </label>
            <select
              class="form-select auto-level-select"
              :value="selectedParty.auto_delve_level ?? 1"
              @change="setAutoDelveLevel(Number(($event.target as HTMLSelectElement).value) || 1)"
            >
              <option v-for="n in maxDungeonLevel" :key="n" :value="n">Depth {{ n }}</option>
            </select>
            <span class="auto-delve-label" style="margin-left: 8px">|</span>
            <label class="checkbox-label">
              <input
                type="checkbox"
                :checked="selectedParty.auto_decide_events"
                @change="togglePartySetting('auto_decide')"
              />
              Auto-Decide Events
            </label>
          </div>
        </template>
        <div v-else class="text-muted">Select a party above</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.formation-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.formation-column {
  min-height: 200px;
}

.adv-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px solid var(--border-color);
}

.adv-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.adv-name {
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.adv-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.stat {
  font-size: 11px;
  font-family: var(--font-mono);
  white-space: nowrap;
  color: var(--text-muted);
}

.stat.xp {
  color: var(--accent-blue, #60a5fa);
}

.auto-delve-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  border-top: 1px solid var(--border-color);
}

.auto-delve-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  accent-color: var(--accent-green);
}

.auto-level-select {
  width: auto;
  min-width: 90px;
  padding: 2px 6px;
  font-size: 11px;
}

.ml-1 {
  margin-left: 8px;
}
</style>
