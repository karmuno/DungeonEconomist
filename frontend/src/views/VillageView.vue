<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as buildingsApi from '../api/buildings'
import * as adventurersApi from '../api/adventurers'
import type { BuildingData } from '../api/buildings'
import type { AdventurerOut } from '../types'
import { useNotificationsStore } from '../stores/notifications'
import { usePlayerStore } from '../stores/player'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import AssignPopover from '../components/village/AssignPopover.vue'
import AdventurerSheetModal from '../components/adventurers/AdventurerSheetModal.vue'

const notifications = useNotificationsStore()
const player = usePlayerStore()

const buildings = ref<BuildingData[]>([])
const adventurers = ref<AdventurerOut[]>([])
const loading = ref(true)
const acting = ref(false)
const sheetAdvId = ref<number | null>(null)

// Which empty slot is showing its assign popover
const pickingSlot = ref<{ buildingType: string; slotIndex: number } | null>(null)

async function fetchAll() {
  buildings.value = await buildingsApi.list()
  adventurers.value = await adventurersApi.list(true)
}

onMounted(async () => {
  await fetchAll()
  await player.fetchPlayer()
  loading.value = false
})

const treasuryCp = computed(() =>
  player.treasuryGold * 100 + player.treasurySilver * 10 + player.treasuryCopper
)

function canAfford(costGp: number | null | undefined): boolean {
  return costGp != null && treasuryCp.value >= costGp * 100
}

function fmtGp(costGp: number): string {
  return `${costGp.toLocaleString('en-US')}gp`
}

interface SlotView {
  index: number
  minLevel: number
  adventurer: BuildingData['assigned_adventurers'][0] | null
}

// Expand tier slots into individual slots; assigned members fill them in
// tier order, the rest are empty with their tier's level requirement.
function slotViews(b: BuildingData): SlotView[] {
  const slots: SlotView[] = []
  let index = 0
  for (const tier of b.tier_slots ?? []) {
    for (let i = 0; i < tier.slots; i++) {
      slots.push({ index: index++, minLevel: tier.min_level, adventurer: null })
    }
  }
  const assigned = [...b.assigned_adventurers].sort((a, x) => a.level - x.level)
  for (const adv of assigned) {
    const slot = slots.find(s => s.adventurer === null && adv.level >= s.minLevel)
      ?? slots.find(s => s.adventurer === null)
    if (slot) slot.adventurer = adv
  }
  return slots
}

function eligibleFor(b: BuildingData, minLevel: number): AdventurerOut[] {
  const allowed = b.allowed_classes ?? [b.adventurer_class]
  return adventurers.value.filter(a =>
    allowed.includes(a.adventurer_class)
    && a.level >= minLevel
    && !a.is_dead
    && !a.is_bankrupt
    && !a.on_expedition
    && !a.is_assigned
  )
}

// What one more assigned adventurer adds, for the popover header
function assignBonus(b: BuildingData): string {
  return b.current_stats.filter(l => l.rate).map(l => `${l.rate} ${l.phrase}`).join(' · ')
}

async function buyBuilding(b: BuildingData) {
  acting.value = true
  try {
    await buildingsApi.buy(b.building_type)
    await fetchAll()
    await player.fetchPlayer()
  } catch (e) {
    notifications.add((e as { data?: { detail?: string } })?.data?.detail ?? 'Failed to build', 'error')
  } finally {
    acting.value = false
  }
}

async function pickAdventurer(b: BuildingData, advId: number) {
  if (b.id == null) return
  pickingSlot.value = null
  acting.value = true
  try {
    await buildingsApi.assign(b.id, advId)
    await fetchAll()
  } catch (e) {
    notifications.add((e as { data?: { detail?: string } })?.data?.detail ?? 'Failed to assign', 'error')
  } finally {
    acting.value = false
  }
}

async function unassign(b: BuildingData, advId: number) {
  if (b.id == null) return
  acting.value = true
  try {
    await buildingsApi.unassign(b.id, advId)
    await fetchAll()
  } catch (e) {
    notifications.add((e as { data?: { detail?: string } })?.data?.detail ?? 'Failed to unassign', 'error')
  } finally {
    acting.value = false
  }
}

function isPicking(b: BuildingData, slotIndex: number): boolean {
  return pickingSlot.value?.buildingType === b.building_type
    && pickingSlot.value?.slotIndex === slotIndex
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
        class="bcard"
        :class="{ unbuilt: b.level === 0 }"
      >
        <!-- Header -->
        <div class="bcard-header">
          <span class="bcard-name">{{ b.name }}</span>
          <span v-if="b.level > 0" class="level-badge">Built</span>
          <span v-else class="level-badge grey">Not Built</span>
          <span class="bcard-class">{{ (b.allowed_classes ?? [b.adventurer_class]).join(' / ') }}</span>
        </div>

        <!-- Every effect, in the dashboard's words: what it delivers now, and what each assignment adds -->
        <div class="stats-block">
          <div v-for="line in b.current_stats" :key="line.phrase" class="stat-row">
            <span class="stat-value" :class="{ muted: !line.active }">{{ line.value }} {{ line.phrase }}</span>
            <span v-if="line.rate" class="stat-rate">{{ line.rate }} each</span>
          </div>
        </div>

        <!-- Assigned -->
        <div v-if="b.level > 0" class="assigned-block">
          <span class="stat-label">Assigned<template v-if="b.slots_free"> · {{ b.slots_free }} free</template></span>
          <div class="assigned-row">
            <template v-for="slot in slotViews(b)" :key="slot.index">
              <span v-if="slot.adventurer" class="adv-chip">
                <span class="adv-link" @click="sheetAdvId = slot.adventurer.id">{{ slot.adventurer.name }}</span>
                <span class="chip-level">Lv {{ slot.adventurer.level }}</span>
                <span class="chip-x" @click="unassign(b, slot.adventurer.id)">×</span>
              </span>
              <span
                v-else
                class="empty-slot"
                @click="pickingSlot = isPicking(b, slot.index) ? null : { buildingType: b.building_type, slotIndex: slot.index }"
              >
                Empty · {{ (b.allowed_classes ?? [b.adventurer_class]).join('/') }} Lv {{ slot.minLevel }}+
                <AssignPopover
                  v-if="isPicking(b, slot.index)"
                  :class-name="(b.allowed_classes ?? [b.adventurer_class]).join(' / ')"
                  :min-level="slot.minLevel"
                  :bonus-label="assignBonus(b)"
                  :candidates="eligibleFor(b, slot.minLevel)"
                  @pick="pickAdventurer(b, $event)"
                  @close="pickingSlot = null"
                />
              </span>
            </template>
          </div>
        </div>

        <!-- What building it will do. Upgrades are hidden for the MVP: tiers
             stay in config and the API, the Village just doesn't offer them. -->
        <div v-if="b.next_stats && b.level === 0" class="next-block">
          <span class="stat-label next-label">
            {{ b.level > 0 ? `Upgrade to ${b.next_name}` : 'When built' }}
          </span>
          <div v-for="line in b.next_stats" :key="line.phrase" class="stat-row">
            <span class="stat-value changed">{{ line.rate ?? line.value }} {{ line.phrase }}</span>
            <span v-if="line.rate" class="stat-rate">each</span>
          </div>
        </div>

        <!-- Action -->
        <button
          v-if="b.level === 0 && b.buy_cost != null"
          class="build-btn"
          :class="{ unaffordable: !canAfford(b.buy_cost) }"
          :disabled="acting || !canAfford(b.buy_cost)"
          @click="buyBuilding(b)"
        >
          Build · {{ fmtGp(b.buy_cost) }}
        </button>
      </div>
    </div>

    <AdventurerSheetModal :adventurer-id="sheetAdvId" @close="sheetAdvId = null" />
  </div>
</template>

<style scoped>
.buildings-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.bcard {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #1f2937;
  border: 1px solid #4b5563;
  border-left: 3px solid #4ade80;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  padding: 12px 16px;
}

.bcard.unbuilt {
  border-left-color: #6b7280;
  border-style: dashed;
  opacity: 0.85;
}

.bcard-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.bcard-name {
  font-size: 14px;
  font-weight: 700;
  color: #4ade80;
}

.level-badge {
  font-size: 9.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 1px 6px;
  border-radius: 4px;
  color: #4ade80;
  background: rgba(74, 222, 128, 0.15);
}

.level-badge.grey {
  color: #6b7280;
  background: rgba(107, 114, 128, 0.15);
}

.bcard-class {
  margin-left: auto;
  font-size: 10px;
  color: #6b7280;
}

/* Stats */
.stats-block {
  min-height: 96px;
}

.stat-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px solid rgba(55, 65, 81, 0.5);
}

.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}

.stat-value {
  font-size: 12px;
  color: #e5e7eb;
}

.stat-rate {
  font-size: 10px;
  color: #6b7280;
}

.stat-value.muted {
  color: #6b7280;
}

.stat-value.changed {
  color: #4ade80;
}

/* Assigned */
.assigned-block {
  min-height: 26px;
}

.assigned-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 3px;
  position: relative;
}

.adv-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  padding: 3px 6px;
  background: rgba(74, 222, 128, 0.08);
  border: 1px solid rgba(74, 222, 128, 0.15);
  border-radius: 3px;
}

.adv-link {
  font-size: 11px;
  color: #e5e7eb;
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: #374151;
  text-underline-offset: 2px;
}

.adv-link:hover {
  text-decoration-color: #4ade80;
}

.chip-level {
  font-size: 10px;
  color: #6b7280;
}

.chip-x {
  font-size: 11px;
  color: #6b7280;
  cursor: pointer;
}

.chip-x:hover {
  color: #ef4444;
}

.empty-slot {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 3px 6px;
  border: 1px dashed #4b5563;
  border-radius: 3px;
  font-size: 10px;
  color: #6b7280;
  cursor: pointer;
  transition: border-color 0.12s, color 0.12s;
}

.empty-slot:hover {
  border-color: #4ade80;
  color: #4ade80;
}

/* Next tier */
.next-block {
  border-top: 1px solid #374151;
  padding-top: 8px;
}

.next-label {
  display: block;
  margin-bottom: 2px;
}

/* Button */
.build-btn {
  margin-top: auto;
  padding: 7px 12px;
  background: #22c55e;
  color: #000;
  border: 1px solid #22c55e;
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.12s;
}

.build-btn:hover:not(:disabled) {
  background: #4ade80;
}

.build-btn.unaffordable {
  background: #1a1a1a;
  border: 1px solid #4b5563;
  color: #6b7280;
  cursor: default;
}
</style>
