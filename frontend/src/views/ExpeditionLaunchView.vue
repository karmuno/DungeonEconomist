<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { PartyOut } from '../types'
import type { DungeonInfo, DungeonLevel } from '../api/game'
import * as partiesApi from '../api/parties'
import * as expeditionsApi from '../api/expeditions'
import * as gameApi from '../api/game'
import { useNotificationsStore } from '../stores/notifications'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import AdventurerLink from '../components/adventurers/AdventurerLink.vue'

const router = useRouter()
const route = useRoute()
const notifications = useNotificationsStore()

const parties = ref<PartyOut[]>([])
const selectedPartyId = ref<number | null>(null)
const dungeon = ref<DungeonInfo | null>(null)
const selectedLevel = ref(1)
const loading = ref(true)
const submitting = ref(false)

const selectedParty = computed<PartyOut | null>(() =>
  parties.value.find(p => p.id === selectedPartyId.value) ?? null
)

const selectedLevelInfo = computed<DungeonLevel | null>(() =>
  dungeon.value?.levels.find(l => l.level === selectedLevel.value) ?? null
)

// Only show parties that aren't on expedition and have members
const availableParties = computed(() =>
  parties.value.filter(p => !p.on_expedition && p.members.length > 0)
)

function partyReadiness(p: PartyOut): string {
  if (p.members.length === 0) return 'Empty'
  if (p.members.every(m => m.hp_current >= m.hp_max)) return 'Ready'
  return 'Healing'
}

function hpColor(current: number, max: number): string {
  const pct = max > 0 ? current / max : 0
  if (pct >= 0.6) return 'var(--accent-green)'
  if (pct >= 0.3) return '#fbbf24'
  return 'var(--accent-red, #e74c3c)'
}

onMounted(async () => {
  try {
    const [partiesData, dungeonData] = await Promise.all([
      partiesApi.list(),
      gameApi.getDungeonInfo(),
    ])
    parties.value = partiesData
    dungeon.value = dungeonData
    selectedLevel.value = dungeonData.max_dungeon_level

    // Pre-select party from route param if provided
    const partyIdParam = Number(route.params.partyId)
    if (partyIdParam && partiesData.some(p => p.id === partyIdParam)) {
      selectedPartyId.value = partyIdParam
    } else if (availableParties.value.length > 0) {
      selectedPartyId.value = availableParties.value[0].id
    }
  } catch {
    notifications.add('Failed to load expedition data', 'error')
    router.push('/')
  }
  loading.value = false
})

async function launchExpedition() {
  if (!selectedParty.value) return
  submitting.value = true
  try {
    await expeditionsApi.launch({
      party_id: selectedParty.value.id,
      dungeon_level: selectedLevel.value,
    })
    notifications.add('Expedition launched!', 'success')
    router.push('/')
  } catch (e: any) {
    const detail = e?.data?.detail ?? 'Failed to launch expedition'
    notifications.add(detail, 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <h1>Launch Expedition</h1>

    <LoadingSpinner v-if="loading" />
    <div v-else class="expedition-layout">
      <!-- Left: Party selection -->
      <div class="card">
        <div class="form-group mb-2">
          <label class="form-label">Party</label>
          <select v-model="selectedPartyId" class="form-select">
            <option :value="null" disabled>Select a party...</option>
            <option
              v-for="p in availableParties"
              :key="p.id"
              :value="p.id"
            >
              {{ p.name }} ({{ p.members.length }}) — {{ partyReadiness(p) }}
            </option>
          </select>
        </div>

        <template v-if="selectedParty">
          <div class="member-list">
            <div v-for="member in selectedParty.members" :key="member.id" class="member-row">
              <AdventurerLink :name="member.name" class="member-name" />
              <span class="badge">{{ member.adventurer_class }}</span>
              <span class="stat">Lv {{ member.level }}</span>
              <span class="stat" :style="{ color: hpColor(member.hp_current, member.hp_max) }">
                {{ member.hp_current }}/{{ member.hp_max }} HP
              </span>
            </div>
          </div>
        </template>
        <div v-else class="text-muted">Select a party to see its members</div>
      </div>

      <!-- Right: Dungeon level selector -->
      <div class="card" v-if="dungeon">
        <h3 class="dungeon-title">{{ dungeon.dungeon_name }}</h3>
        <p class="text-muted mb-2" style="font-size: 12px">Choose a depth to explore</p>

        <div class="level-list">
          <button
            v-for="dl in dungeon.levels"
            :key="dl.level"
            class="level-btn"
            :class="{
              selected: dl.level === selectedLevel,
              locked: !dl.unlocked,
              unlocked: dl.unlocked,
            }"
            :disabled="!dl.unlocked"
            @click="dl.unlocked && (selectedLevel = dl.level)"
          >
            <span class="level-num">{{ dl.level }}</span>
            <span class="level-name">{{ dl.unlocked ? dl.name : '???' }}</span>
            <span v-if="dl.unlocked" class="level-days">{{ dl.duration_days }}d</span>
            <span v-else class="level-lock">&#x1f512;</span>
          </button>
        </div>

        <div v-if="selectedLevelInfo" class="selected-info mt-2">
          <div class="selected-depth">
            Depth {{ selectedLevelInfo.level }} &mdash; {{ selectedLevelInfo.name }}
          </div>
          <div class="text-muted" style="font-size: 12px">
            Duration: {{ selectedLevelInfo.duration_days }} day{{ selectedLevelInfo.duration_days !== 1 ? 's' : '' }}
          </div>
        </div>

        <div class="mt-2 flex gap-1">
          <button
            class="btn btn-primary"
            :disabled="submitting || !selectedParty || !selectedLevelInfo?.unlocked"
            @click="launchExpedition"
          >
            {{ submitting ? 'Launching...' : 'Descend' }}
          </button>
          <button
            class="btn btn-secondary"
            @click="router.push('/')"
          >
            Not Now
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.expedition-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  max-width: 800px;
}

.dungeon-title {
  color: var(--accent-green);
  font-size: 1.2rem;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
}

.member-name {
  font-weight: 600;
  font-size: 13px;
  flex: 1;
}

.stat {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  white-space: nowrap;
}

.level-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.level-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-primary);
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}

.level-btn.unlocked:hover {
  border-color: var(--accent-green);
  background: var(--bg-tertiary, var(--bg-secondary));
}

.level-btn.selected {
  border-color: var(--accent-green);
  background: rgba(74, 222, 128, 0.08);
}

.level-btn.locked {
  opacity: 0.4;
  cursor: not-allowed;
}

.level-num {
  font-weight: 700;
  font-size: 16px;
  color: var(--accent-green);
  width: 24px;
  text-align: center;
}

.level-btn.locked .level-num {
  color: var(--text-muted);
}

.level-name {
  flex: 1;
}

.level-days {
  font-size: 11px;
  color: var(--text-muted);
}

.level-lock {
  font-size: 14px;
}

.selected-info {
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.selected-depth {
  font-weight: 700;
  color: var(--accent-green);
}
</style>
