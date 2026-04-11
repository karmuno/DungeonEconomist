<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { AdventurerOut, PartyOut } from '../types'
import * as adventurersApi from '../api/adventurers'
import * as partiesApi from '../api/parties'
import { useNotificationsStore } from '../stores/notifications'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import AdventurerLink from '../components/adventurers/AdventurerLink.vue'

const router = useRouter()
const notifications = useNotificationsStore()

const allAdventurers = ref<AdventurerOut[]>([])
const existingParties = ref<PartyOut[]>([])
const selectedMembers = ref<AdventurerOut[]>([])
const partyName = ref('')
const classFilter = ref('')
const loading = ref(true)
const submitting = ref(false)

const MAX_PARTY_SIZE = 6

// IDs of adventurers already in any existing party
const affiliatedIds = computed(() => {
  const ids = new Set<number>()
  for (const p of existingParties.value) {
    for (const m of p.members) {
      ids.add(m.id)
    }
  }
  return ids
})

const selectedIds = computed(() => new Set(selectedMembers.value.map((m) => m.id)))

const availableAdventurers = computed(() => {
  return allAdventurers.value.filter((a) => {
    if (selectedIds.value.has(a.id)) return false
    if (affiliatedIds.value.has(a.id)) return false
    if (!a.is_available || a.on_expedition || a.is_assigned || a.is_dead || a.is_bankrupt) return false
    if (classFilter.value && a.adventurer_class !== classFilter.value) return false
    return true
  })
})

const canSubmit = computed(() =>
  partyName.value.trim().length > 0 && selectedMembers.value.length > 0 && !submitting.value
)

onMounted(async () => {
  allAdventurers.value = await adventurersApi.list()
  existingParties.value = await partiesApi.list()
  loading.value = false
})

function addMember(adv: AdventurerOut) {
  if (selectedMembers.value.length >= MAX_PARTY_SIZE) return
  selectedMembers.value.push(adv)
}

function removeMember(id: number) {
  selectedMembers.value = selectedMembers.value.filter((m) => m.id !== id)
}

function hpColor(adv: AdventurerOut): string {
  const pct = adv.hp_max > 0 ? adv.hp_current / adv.hp_max : 0
  if (pct >= 0.6) return 'var(--accent-green)'
  if (pct >= 0.3) return '#fbbf24'
  return 'var(--accent-red, #e74c3c)'
}

async function formParty() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    const party = await partiesApi.create({ name: partyName.value.trim() })
    for (const member of selectedMembers.value) {
      await partiesApi.addMember({ party_id: party.id, adventurer_id: member.id })
    }
    notifications.add(`Party "${party.name}" formed with ${selectedMembers.value.length} members`, 'success')
    router.push(`/launch-expedition/${party.id}`)
  } catch {
    notifications.add('Failed to form party', 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <h1>Form a Party</h1>

    <LoadingSpinner v-if="loading" />
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
        <div v-if="availableAdventurers.length === 0" class="text-muted">No available adventurers</div>
        <div
          v-for="adv in availableAdventurers"
          :key="adv.id"
          class="adv-row"
        >
          <div class="adv-main">
            <AdventurerLink :adv-name="adv.name" class="adv-name" />
            <span class="badge">{{ adv.adventurer_class }}</span>
          </div>
          <div class="adv-stats">
            <span class="stat">Lv {{ adv.level }}</span>
            <span class="stat" :style="{ color: hpColor(adv) }">{{ adv.hp_current }}/{{ adv.hp_max }} HP</span>
            <span class="stat xp">{{ adv.xp }}<template v-if="adv.next_level_xp"> / {{ adv.next_level_xp }}</template> XP</span>
          </div>
          <button
            class="btn btn-primary btn-sm"
            :disabled="selectedMembers.length >= MAX_PARTY_SIZE"
            @click="addMember(adv)"
          >
            +
          </button>
        </div>
      </div>

      <!-- Right: Party Members -->
      <div class="formation-column card">
        <h3 class="mb-2">Party Members ({{ selectedMembers.length }}/{{ MAX_PARTY_SIZE }})</h3>
        <div class="form-group mb-2">
          <input
            v-model="partyName"
            class="form-input"
            type="text"
            placeholder="Party name..."
            required
          />
        </div>
        <div v-if="selectedMembers.length === 0" class="text-muted">Add adventurers from the left</div>
        <div
          v-for="member in selectedMembers"
          :key="member.id"
          class="adv-row"
        >
          <div class="adv-main">
            <AdventurerLink :adv-name="member.name" class="adv-name" />
            <span class="badge">{{ member.adventurer_class }}</span>
          </div>
          <div class="adv-stats">
            <span class="stat">Lv {{ member.level }}</span>
            <span class="stat" :style="{ color: hpColor(member) }">{{ member.hp_current }}/{{ member.hp_max }} HP</span>
            <span class="stat xp">{{ member.xp }} XP</span>
          </div>
          <button
            class="btn btn-danger btn-sm"
            @click="removeMember(member.id)"
          >
            &times;
          </button>
        </div>
        <div class="mt-3">
          <button
            class="btn btn-primary"
            :disabled="!canSubmit"
            @click="formParty"
          >
            Form Party
          </button>
          <button
            class="btn btn-secondary ml-1"
            @click="router.push('/')"
          >
            Cancel
          </button>
        </div>
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

.ml-1 {
  margin-left: 8px;
}
</style>
