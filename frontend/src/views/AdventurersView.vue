<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { AdventurerOut, PartyOut } from '../types'
import * as adventurersApi from '../api/adventurers'
import * as partiesApi from '../api/parties'
import type { GraveyardEntry, DebtorEntry } from '../api/adventurers'
import { useNotificationsStore } from '../stores/notifications'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import EmptyState from '../components/shared/EmptyState.vue'
import ModalDialog from '../components/shared/ModalDialog.vue'
import AdventurerFilters from '../components/adventurers/AdventurerFilters.vue'
import AdventurerCard from '../components/adventurers/AdventurerCard.vue'
import AdventurerList from '../components/adventurers/AdventurerList.vue'
import AdventurerDetail from '../components/adventurers/AdventurerDetail.vue'
import { formatCurrency } from '../utils/currency'
import { formatGameDay } from '../utils/calendar'

const router = useRouter()
const notifications = useNotificationsStore()

const activeTab = ref<'roster' | 'graveyard' | 'debtors'>('roster')
const adventurers = ref<AdventurerOut[]>([])
const parties = ref<PartyOut[]>([])
const graveyard = ref<GraveyardEntry[]>([])
const debtors = ref<DebtorEntry[]>([])
const loading = ref(true)
const viewMode = ref<'card' | 'list'>('card')
const selectedAdventurer = ref<AdventurerOut | null>(null)
const showDetail = ref(false)

// Party management in adventurer modal
const selectedPartyId = ref<number | null>(null)
const managingParty = ref(false)

const filters = ref({
  classFilter: '',
  statusFilter: '',
  nameSearch: '',
  sortBy: 'name',
  sortDir: 'asc' as 'asc' | 'desc',
})

const filteredAdventurers = computed(() => {
  let result = [...adventurers.value]

  if (filters.value.classFilter) {
    result = result.filter((a) => a.adventurer_class === filters.value.classFilter)
  }

  if (filters.value.statusFilter) {
    switch (filters.value.statusFilter) {
      case 'available':
        result = result.filter((a) => a.is_available && !a.on_expedition)
        break
      case 'on_expedition':
        result = result.filter((a) => a.on_expedition)
        break
      case 'injured':
        result = result.filter((a) => a.hp_current < a.hp_max)
        break
    }
  }

  if (filters.value.nameSearch) {
    const search = filters.value.nameSearch.toLowerCase()
    result = result.filter((a) => a.name.toLowerCase().includes(search))
  }

  const dir = filters.value.sortDir === 'asc' ? 1 : -1
  const sortKey = filters.value.sortBy as keyof AdventurerOut

  result.sort((a, b) => {
    const aVal = a[sortKey]
    const bVal = b[sortKey]
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return dir * aVal.localeCompare(bVal)
    }
    return dir * (Number(aVal) - Number(bVal))
  })

  return result
})

// Find which party an adventurer belongs to
function adventurerParty(advId: number): PartyOut | undefined {
  return parties.value.find((p) => p.members.some((m) => m.id === advId))
}

// Parties that can accept a new member
const availableParties = computed(() =>
  parties.value.filter((p) => p.members.length < 6 && !p.on_expedition)
)

async function fetchAdventurers() {
  loading.value = true
  try {
    adventurers.value = await adventurersApi.list()
    parties.value = await partiesApi.list()
  } finally {
    loading.value = false
  }
}

async function fetchGraveyard() {
  graveyard.value = await adventurersApi.getGraveyard()
}

async function fetchDebtors() {
  debtors.value = await adventurersApi.getDebtorsPrison()
}

async function onTabChange(tab: 'roster' | 'graveyard' | 'debtors') {
  activeTab.value = tab
  if (tab === 'graveyard') await fetchGraveyard()
  if (tab === 'debtors') await fetchDebtors()
}

async function onSelect(id: number) {
  try {
    selectedAdventurer.value = await adventurersApi.getById(id)
    selectedPartyId.value = null
    managingParty.value = false
    showDetail.value = true
  } catch {
    notifications.add('Failed to load adventurer details', 'error')
  }
}

async function onLevelUp() {
  if (!selectedAdventurer.value) return
  try {
    const result = await adventurersApi.levelUp(selectedAdventurer.value.id)
    notifications.add(
      `${selectedAdventurer.value.name} leveled up to ${result.new_level}! HP gained: ${result.hp_gained}`,
      'success'
    )
    selectedAdventurer.value = await adventurersApi.getById(selectedAdventurer.value.id)
    await fetchAdventurers()
  } catch {
    notifications.add('Level up failed', 'error')
  }
}

async function removeFromParty() {
  if (!selectedAdventurer.value) return
  const party = adventurerParty(selectedAdventurer.value.id)
  if (!party) return
  try {
    await partiesApi.removeMember({ party_id: party.id, adventurer_id: selectedAdventurer.value.id })
    notifications.add(`Removed ${selectedAdventurer.value.name} from ${party.name}`, 'success')
    await fetchAdventurers()
  } catch {
    notifications.add('Failed to remove from party', 'error')
  }
}

async function addToParty() {
  if (!selectedAdventurer.value || !selectedPartyId.value) return
  try {
    await partiesApi.addMember({ party_id: selectedPartyId.value, adventurer_id: selectedAdventurer.value.id })
    const partyName = parties.value.find((p) => p.id === selectedPartyId.value)?.name ?? 'party'
    notifications.add(`Added ${selectedAdventurer.value.name} to ${partyName}`, 'success')
    selectedPartyId.value = null
    await fetchAdventurers()
  } catch {
    notifications.add('Failed to add to party', 'error')
  }
}

onMounted(fetchAdventurers)
</script>

<template>
  <div>
    <div class="flex flex-between mb-3">
      <h1>Tavern</h1>
      <button class="btn btn-primary" @click="router.push('/form-party')">
        Form Party
      </button>
    </div>

    <div class="flex flex-between mb-2">
      <div class="view-toggle">
        <button
          class="btn btn-sm"
          :class="activeTab === 'roster' ? 'btn-primary' : 'btn-secondary'"
          @click="onTabChange('roster')"
        >
          Roster
        </button>
        <button
          class="btn btn-sm"
          :class="activeTab === 'graveyard' ? 'btn-primary' : 'btn-secondary'"
          @click="onTabChange('graveyard')"
        >
          Graveyard
        </button>
        <button
          class="btn btn-sm"
          :class="activeTab === 'debtors' ? 'btn-primary' : 'btn-secondary'"
          @click="onTabChange('debtors')"
        >
          Debtor's Prison
        </button>
      </div>
      <div v-if="activeTab === 'roster'" class="view-toggle">
        <button
          class="btn btn-sm"
          :class="{ 'btn-primary': viewMode === 'card' }"
          @click="viewMode = 'card'"
        >
          Cards
        </button>
        <button
          class="btn btn-sm"
          :class="{ 'btn-primary': viewMode === 'list' }"
          @click="viewMode = 'list'"
        >
          List
        </button>
      </div>
    </div>

    <!-- Roster Tab -->
    <template v-if="activeTab === 'roster'">
      <AdventurerFilters v-model="filters" class="mb-3" />

      <LoadingSpinner v-if="loading" />
      <template v-else>
        <template v-if="filteredAdventurers.length > 0">
          <div v-if="viewMode === 'card'" class="stats-grid">
            <AdventurerCard
              v-for="adv in filteredAdventurers"
              :key="adv.id"
              :adventurer="adv"
              @select="onSelect"
            />
          </div>
          <AdventurerList
            v-else
            :adventurers="filteredAdventurers"
            @select="onSelect"
          />
        </template>
        <EmptyState v-else message="No adventurers match your filters" />
      </template>
    </template>

    <!-- Graveyard Tab -->
    <template v-if="activeTab === 'graveyard'">
      <EmptyState v-if="graveyard.length === 0" message="No fallen adventurers" />
      <table v-else class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Class</th>
            <th>Level</th>
            <th>Died On</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in graveyard" :key="entry.id">
            <td>{{ entry.name }}</td>
            <td>{{ entry.class }}</td>
            <td>{{ entry.level }}</td>
            <td>{{ formatGameDay(entry.death_day) }}</td>
          </tr>
        </tbody>
      </table>
    </template>

    <!-- Debtor's Prison Tab -->
    <template v-if="activeTab === 'debtors'">
      <EmptyState v-if="debtors.length === 0" message="No bankrupt adventurers" />
      <table v-else class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Class</th>
            <th>Level</th>
            <th>Bankrupt On</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in debtors" :key="entry.id">
            <td>{{ entry.name }}</td>
            <td>{{ entry.class }}</td>
            <td>{{ entry.level }}</td>
            <td>{{ formatGameDay(entry.bankruptcy_day) }}</td>
          </tr>
        </tbody>
      </table>
    </template>

    <!-- Adventurer Detail Modal with Party Management -->
    <ModalDialog
      :is-open="showDetail"
      :title="selectedAdventurer?.name ?? 'Adventurer'"
      @close="showDetail = false"
    >
      <template v-if="selectedAdventurer">
        <AdventurerDetail
          :adventurer="selectedAdventurer"
          @close="showDetail = false"
          @level-up="onLevelUp"
        />

        <!-- Party Management Section -->
        <div class="party-management mt-3" style="border-top: 1px solid var(--border-color); padding-top: 16px">
          <h4 class="mb-2">Party Assignment</h4>
          <template v-if="adventurerParty(selectedAdventurer.id)">
            <p class="mb-1">
              Currently in: <strong>{{ adventurerParty(selectedAdventurer.id)!.name }}</strong>
            </p>
            <button
              class="btn btn-danger btn-sm"
              :disabled="selectedAdventurer.on_expedition"
              @click="removeFromParty"
            >
              Remove from Party
            </button>
          </template>
          <template v-else-if="selectedAdventurer.is_available && !selectedAdventurer.on_expedition && !selectedAdventurer.is_dead && !selectedAdventurer.is_bankrupt">
            <div class="flex gap-1">
              <select v-model="selectedPartyId" class="form-select">
                <option :value="null" disabled>Add to party...</option>
                <option
                  v-for="p in availableParties"
                  :key="p.id"
                  :value="p.id"
                >
                  {{ p.name }} ({{ p.members.length }}/6)
                </option>
              </select>
              <button
                class="btn btn-primary btn-sm"
                :disabled="!selectedPartyId"
                @click="addToParty"
              >
                Add
              </button>
            </div>
          </template>
          <p v-else class="text-muted">Not available for party assignment</p>
        </div>
      </template>
    </ModalDialog>
  </div>
</template>
