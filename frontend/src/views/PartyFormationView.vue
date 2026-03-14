<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { AdventurerOut, PartyOut } from '../types'
import * as adventurersApi from '../api/adventurers'
import * as partiesApi from '../api/parties'
import { useNotificationsStore } from '../stores/notifications'
import ProgressBar from '../components/shared/ProgressBar.vue'
import StatusBadge from '../components/shared/StatusBadge.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import { formatCurrency } from '../utils/currency'
import { displayStatus } from '../utils/adventurer'

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
    if (!a.is_available || a.on_expedition || a.is_dead || a.is_bankrupt) return false
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
    <h1 class="mb-3">Form a Party</h1>

    <LoadingSpinner v-if="loading" />
    <div v-else class="formation-layout">
      <!-- Left: Available Adventurers -->
      <div class="formation-column card">
        <h3 class="mb-2">Available Adventurers</h3>
        <div class="filters-bar mb-2">
          <select v-model="classFilter" class="form-select">
            <option value="">All Classes</option>
            <option v-for="cls in ['Fighter', 'Cleric', 'Magic-User', 'Elf', 'Dwarf', 'Hobbit']" :key="cls" :value="cls">
              {{ cls }}
            </option>
          </select>
        </div>
        <div v-if="availableAdventurers.length === 0" class="text-muted">No available adventurers</div>
        <div
          v-for="adv in availableAdventurers"
          :key="adv.id"
          class="formation-row"
        >
          <div class="formation-info">
            <strong>{{ adv.name }}</strong>
            <span class="badge">{{ adv.adventurer_class }}</span>
            <span class="text-muted">Lv {{ adv.level }}</span>
          </div>
          <div class="formation-meta">
            <ProgressBar :value="adv.hp_current" :max="adv.hp_max" />
            <StatusBadge :status="displayStatus(adv)" />
          </div>
          <button
            class="btn btn-primary btn-sm"
            :disabled="selectedMembers.length >= MAX_PARTY_SIZE"
            @click="addMember(adv)"
          >
            Add &rarr;
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
          class="formation-row"
        >
          <div class="formation-info">
            <strong>{{ member.name }}</strong>
            <span class="badge">{{ member.adventurer_class }}</span>
            <span class="text-muted">Lv {{ member.level }}</span>
          </div>
          <button
            class="btn btn-danger btn-sm"
            @click="removeMember(member.id)"
          >
            &larr; Remove
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

.formation-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
}

.formation-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.formation-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.ml-1 {
  margin-left: 8px;
}
</style>
