<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { AdventurerOut, PartyOut } from '../types'
import * as adventurersApi from '../api/adventurers'
import * as partiesApi from '../api/parties'
import { useNotificationsStore } from '../stores/notifications'
import { useGameTimeStore } from '../stores/gameTime'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import EmptyState from '../components/shared/EmptyState.vue'
import ModalDialog from '../components/shared/ModalDialog.vue'
import AdventurerFilters from '../components/adventurers/AdventurerFilters.vue'
import AdventurerList from '../components/adventurers/AdventurerList.vue'
import AdventurerDetail from '../components/adventurers/AdventurerDetail.vue'
import { displayStatus } from '../utils/adventurer'

const router = useRouter()
const notifications = useNotificationsStore()
const gameTime = useGameTimeStore()

watch(() => gameTime.expeditionVersion, () => {
  fetchAll()
})

const activeTab = ref<'roster' | 'graveyard' | 'debtors'>('roster')
const adventurers = ref<AdventurerOut[]>([])
const parties = ref<PartyOut[]>([])
const graveyard = ref<AdventurerOut[]>([])
const debtors = ref<AdventurerOut[]>([])
const loading = ref(true)
const selectedAdventurer = ref<AdventurerOut | null>(null)
const showDetail = ref(false)

const selectedPartyId = ref<number | null>(null)
const confirmingDisband = ref(false)

// Default roster: every living adventurer. Dead and bankrupt have their own tabs.
const DEFAULT_STATUSES = new Set(['Available', 'Recovering', 'On Expedition', 'Assigned'])

function makeFilters(statuses: Set<string> = new Set()) {
  return {
    classFilter: '',
    statuses,
    nameSearch: '',
    sortBy: 'name',
    sortDir: 'asc' as 'asc' | 'desc',
  }
}
type ViewFilters = ReturnType<typeof makeFilters>

const filters = ref(makeFilters(new Set(DEFAULT_STATUSES)))
const graveyardFilters = ref(makeFilters())
const debtorFilters = ref(makeFilters())

/**
 * Shared filter + sort for all three tabs. Status is only meaningful on the Roster;
 * the other two tabs hold exactly one status, so they opt out.
 */
function applyFilters(
  list: AdventurerOut[],
  f: ViewFilters,
  opts: { useStatus?: boolean; partyName?: (a: AdventurerOut) => string } = {},
): AdventurerOut[] {
  let result = [...list]

  if (opts.useStatus && f.statuses.size > 0) {
    result = result.filter((a) => f.statuses.has(displayStatus(a)))
  }

  if (f.classFilter) {
    result = result.filter((a) => a.adventurer_class === f.classFilter)
  }

  if (f.nameSearch) {
    const search = f.nameSearch.toLowerCase()
    result = result.filter((a) => a.name.toLowerCase().includes(search))
  }

  const dir = f.sortDir === 'asc' ? 1 : -1
  const sortKey = f.sortBy
  const partyName = opts.partyName ?? (() => '')

  result.sort((a, b) => {
    if (sortKey === 'party') {
      return dir * partyName(a).localeCompare(partyName(b))
    }
    const aVal = a[sortKey as keyof AdventurerOut]
    const bVal = b[sortKey as keyof AdventurerOut]
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return dir * aVal.localeCompare(bVal)
    }
    return dir * (Number(aVal) - Number(bVal))
  })

  return result
}

const filteredAdventurers = computed(() =>
  applyFilters(adventurers.value, filters.value, {
    useStatus: true,
    partyName: (a) => partyNameMap.value[a.id] ?? '',
  }),
)

// On the Graveyard, "Party" means the party they died with, not a current one.
const filteredGraveyard = computed(() =>
  applyFilters(graveyard.value, graveyardFilters.value, {
    partyName: (a) => a.death_party_name ?? '',
  }),
)

const filteredDebtors = computed(() => applyFilters(debtors.value, debtorFilters.value))

const partyNameMap = computed(() => {
  const map: Record<number, string> = {}
  for (const p of parties.value) {
    for (const m of p.members) {
      map[m.id] = p.name
    }
  }
  return map
})

const availableParties = computed(() =>
  parties.value.filter((p) => p.members.length < 6 && !p.on_expedition)
)

function adventurerParty(advId: number): PartyOut | undefined {
  return parties.value.find((p) => p.members.some((m) => m.id === advId))
}

async function fetchAll() {
  loading.value = true
  try {
    adventurers.value = await adventurersApi.list()
    parties.value = await partiesApi.list()
    if (activeTab.value === 'graveyard') fetchGraveyard()
    if (activeTab.value === 'debtors') fetchDebtors()
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
    confirmingDisband.value = false
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
    await fetchAll()
  } catch {
    notifications.add('Level up failed', 'error')
  }
}

async function removeFromParty() {
  if (!selectedAdventurer.value) return
  const party = adventurerParty(selectedAdventurer.value.id)
  if (!party) return

  if (party.members.length <= 1) {
    if (!confirmingDisband.value) {
      confirmingDisband.value = true
      return
    }
    try {
      await partiesApi.deleteParty(party.id)
      notifications.add(`Party "${party.name}" disbanded`, 'info')
      confirmingDisband.value = false
      await fetchAll()
    } catch {
      notifications.add('Failed to disband party', 'error')
      confirmingDisband.value = false
    }
    return
  }

  try {
    await partiesApi.removeMember({ party_id: party.id, adventurer_id: selectedAdventurer.value.id })
    notifications.add(`Removed ${selectedAdventurer.value.name} from ${party.name}`, 'success')
    await fetchAll()
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
    await fetchAll()
  } catch {
    notifications.add('Failed to add to party', 'error')
  }
}

onMounted(fetchAll)
</script>

<template>
  <div>
    <div class="flex flex-between">
      <h1>Tavern</h1>
      <button class="btn btn-primary" @click="router.push('/form-party')">
        Form Party
      </button>
    </div>

    <div class="view-toggle mb-2">
      <button
        :class="{ active: activeTab === 'roster' }"
        @click="onTabChange('roster')"
      >
        Roster
      </button>
      <button
        :class="{ active: activeTab === 'graveyard' }"
        @click="onTabChange('graveyard')"
      >
        Graveyard
      </button>
      <button
        :class="{ active: activeTab === 'debtors' }"
        @click="onTabChange('debtors')"
      >
        Debtor's Prison
      </button>
    </div>

    <!-- Roster Tab -->
    <template v-if="activeTab === 'roster'">
      <AdventurerFilters v-model="filters" class="mb-2" />

      <LoadingSpinner v-if="loading" />
      <template v-else>
        <template v-if="filteredAdventurers.length > 0">
          <AdventurerList
            :adventurers="filteredAdventurers"
            :party-name-map="partyNameMap"
            @select="onSelect"
          />
        </template>
        <EmptyState v-else message="No adventurers match your filters" />
      </template>
    </template>

    <!-- Graveyard Tab -->
    <template v-if="activeTab === 'graveyard'">
      <EmptyState v-if="graveyard.length === 0" message="No fallen adventurers" />
      <template v-else>
        <AdventurerFilters v-model="graveyardFilters" hide-status class="mb-2" />
        <AdventurerList
          v-if="filteredGraveyard.length > 0"
          :adventurers="filteredGraveyard"
          :hide-hp="true"
          @select="onSelect"
        />
        <EmptyState v-else message="No adventurers match your filters" />
      </template>
    </template>

    <!-- Debtor's Prison Tab -->
    <template v-if="activeTab === 'debtors'">
      <EmptyState v-if="debtors.length === 0" message="No bankrupt adventurers" />
      <template v-else>
        <AdventurerFilters v-model="debtorFilters" hide-status class="mb-2" />
        <AdventurerList
          v-if="filteredDebtors.length > 0"
          :adventurers="filteredDebtors"
          @select="onSelect"
        />
        <EmptyState v-else message="No adventurers match your filters" />
      </template>
    </template>

    <!-- Adventurer Detail Modal -->
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
              {{ confirmingDisband ? 'This will disband the party. Are you sure?' : 'Remove from Party' }}
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
