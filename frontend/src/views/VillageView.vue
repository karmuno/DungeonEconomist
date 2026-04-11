<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as buildingsApi from '../api/buildings'
import * as adventurersApi from '../api/adventurers'
import type { BuildingData } from '../api/buildings'
import type { AdventurerOut } from '../types'
import { useNotificationsStore } from '../stores/notifications'
import { usePlayerStore } from '../stores/player'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const notifications = useNotificationsStore()
const player = usePlayerStore()

const buildings = ref<BuildingData[]>([])
const adventurers = ref<AdventurerOut[]>([])
const loading = ref(true)
const acting = ref(false)

// Which building is currently showing the assign dropdown
const assigningBuildingId = ref<number | null>(null)
const selectedAdventurerId = ref<number | null>(null)

async function fetchAll() {
  buildings.value = await buildingsApi.list()
  adventurers.value = await adventurersApi.list(true)
}

onMounted(async () => {
  await fetchAll()
  loading.value = false
})

function eligibleAdventurers(building: BuildingData): AdventurerOut[] {
  return adventurers.value.filter(a =>
    a.adventurer_class === building.adventurer_class
    && a.level >= building.min_adventurer_level
    && a.is_available
    && !a.on_expedition
    && !a.is_assigned
    && !a.is_dead
    && !a.is_bankrupt
  )
}

async function buyBuilding(btype: string) {
  acting.value = true
  try {
    await buildingsApi.buy(btype)
    await fetchAll()
    await player.fetchPlayer()
    notifications.add('Building constructed!', 'success')
  } catch (e: any) {
    notifications.add(e?.data?.detail ?? 'Failed to buy building', 'error')
  } finally {
    acting.value = false
  }
}

async function upgradeBuilding(buildingId: number) {
  acting.value = true
  try {
    await buildingsApi.upgrade(buildingId)
    await fetchAll()
    await player.fetchPlayer()
    notifications.add('Building upgraded!', 'success')
  } catch (e: any) {
    notifications.add(e?.data?.detail ?? 'Failed to upgrade', 'error')
  } finally {
    acting.value = false
  }
}

async function assignAdventurer(buildingId: number) {
  if (!selectedAdventurerId.value) return
  const adv = adventurers.value.find(a => a.id === selectedAdventurerId.value)
  const bld = buildings.value.find(b => b.id === buildingId)
  acting.value = true
  try {
    await buildingsApi.assign(buildingId, selectedAdventurerId.value)
    selectedAdventurerId.value = null
    assigningBuildingId.value = null
    await fetchAll()
    notifications.add(`${adv?.name ?? 'Adventurer'} assigned to ${bld?.name ?? 'building'}`, 'success')
  } catch (e: any) {
    notifications.add(e?.data?.detail ?? 'Failed to assign', 'error')
  } finally {
    acting.value = false
  }
}

async function unassignAdventurer(buildingId: number, advId: number) {
  acting.value = true
  try {
    await buildingsApi.unassign(buildingId, advId)
    await fetchAll()
    notifications.add('Adventurer returned to tavern', 'info')
  } catch (e: any) {
    notifications.add(e?.data?.detail ?? 'Failed to unassign', 'error')
  } finally {
    acting.value = false
  }
}
</script>

<template>
  <div>
    <h1>Village</h1>

    <LoadingSpinner v-if="loading" />
    <div v-else class="buildings-grid">
      <div
        v-for="b in buildings"
        :key="b.building_type"
        class="building-card card"
        :class="{ unbuilt: b.level === 0 }"
      >
        <!-- Header -->
        <div class="building-header">
          <div>
            <h3 class="building-name">{{ b.name }}</h3>
            <span v-if="b.level > 0" class="building-level">Level {{ b.level }}</span>
          </div>
          <span class="badge">{{ b.adventurer_class }}</span>
        </div>

        <p class="building-desc">{{ b.description }}</p>

        <!-- Current effects -->
        <div v-if="b.effects && b.effects.length > 0" class="building-effects">
          <span v-for="(effect, i) in b.effects" :key="i" class="effect-tag">{{ effect }}</span>
        </div>

        <!-- Not built yet -->
        <template v-if="b.level === 0">
          <div class="building-action">
            <button
              class="btn btn-primary"
              :disabled="acting"
              @click="buyBuilding(b.building_type)"
            >
              Build ({{ b.buy_cost }}gp)
            </button>
          </div>
        </template>

        <!-- Built -->
        <template v-else>
          <p class="bonus-desc">{{ b.assigned_bonus_desc }}</p>

          <!-- Assigned adventurers -->
          <div class="assigned-list">
            <div
              v-for="adv in b.assigned_adventurers"
              :key="adv.id"
              class="assigned-row"
            >
              <span class="assigned-name">{{ adv.name }}</span>
              <span class="stat">Lv {{ adv.level }}</span>
              <button
                class="btn btn-sm btn-danger"
                :disabled="acting"
                @click="unassignAdventurer(b.id!, adv.id)"
              >
                &times;
              </button>
            </div>
            <div v-if="b.assigned_adventurers.length === 0" class="text-muted" style="font-size: 12px">
              No one assigned
            </div>
          </div>

          <!-- Assign slot -->
          <div v-if="b.assigned_adventurers.length < b.max_assigned" class="assign-controls">
            <div v-if="assigningBuildingId === b.id" class="flex gap-1">
              <select v-model="selectedAdventurerId" class="form-select" style="flex:1">
                <option :value="null" disabled>Choose {{ b.adventurer_class }}...</option>
                <option
                  v-for="a in eligibleAdventurers(b)"
                  :key="a.id"
                  :value="a.id"
                >
                  {{ a.name }} (Lv {{ a.level }})
                </option>
              </select>
              <button
                class="btn btn-primary btn-sm"
                :disabled="!selectedAdventurerId || acting"
                @click="assignAdventurer(b.id!)"
              >
                Assign
              </button>
              <button
                class="btn btn-secondary btn-sm"
                @click="assigningBuildingId = null; selectedAdventurerId = null"
              >
                Cancel
              </button>
            </div>
            <button
              v-else
              class="btn btn-sm btn-secondary"
              @click="assigningBuildingId = b.id; selectedAdventurerId = null"
            >
              + Assign {{ b.adventurer_class }} ({{ b.assigned_adventurers.length }}/{{ b.max_assigned }})
            </button>
          </div>
          <div v-else class="text-muted" style="font-size: 11px">
            Full ({{ b.max_assigned }}/{{ b.max_assigned }})
          </div>

          <!-- Upgrade -->
          <div v-if="b.upgrade_cost" class="building-action">
            <button
              class="btn btn-sm btn-primary"
              :disabled="acting"
              @click="upgradeBuilding(b.id!)"
            >
              Upgrade to {{ b.next_name }} ({{ b.upgrade_cost }}gp)
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.buildings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.building-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.building-card.unbuilt {
  opacity: 0.7;
  border-style: dashed;
}

.building-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.building-name {
  font-size: 1.1rem;
  margin: 0;
}

.building-level {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.building-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0;
}

.bonus-desc {
  font-size: 12px;
  color: var(--accent-green);
  margin: 0;
  font-style: italic;
}

.assigned-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.assigned-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
}

.assigned-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
}

.stat {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.assign-controls {
  margin-top: 4px;
}

.building-action {
  margin-top: 4px;
}

.building-effects {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.effect-tag {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--accent-green);
  background: rgba(74, 222, 128, 0.08);
  padding: 2px 8px;
  border-radius: var(--border-radius);
  border: 1px solid rgba(74, 222, 128, 0.15);
}
</style>
