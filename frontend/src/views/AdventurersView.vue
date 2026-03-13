<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { AdventurerOut } from '../types'
import * as adventurersApi from '../api/adventurers'
import type { GraveyardEntry, DebtorEntry } from '../api/adventurers'
import { useNotificationsStore } from '../stores/notifications'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import EmptyState from '../components/shared/EmptyState.vue'
import ModalDialog from '../components/shared/ModalDialog.vue'
import AdventurerFilters from '../components/adventurers/AdventurerFilters.vue'
import AdventurerCard from '../components/adventurers/AdventurerCard.vue'
import AdventurerList from '../components/adventurers/AdventurerList.vue'
import AdventurerDetail from '../components/adventurers/AdventurerDetail.vue'

const notifications = useNotificationsStore()

const activeTab = ref<'roster' | 'graveyard' | 'debtors'>('roster')
const adventurers = ref<AdventurerOut[]>([])
const graveyard = ref<GraveyardEntry[]>([])
const debtors = ref<DebtorEntry[]>([])
const loading = ref(true)
const viewMode = ref<'card' | 'list'>('card')
const selectedAdventurer = ref<AdventurerOut | null>(null)
const showDetail = ref(false)

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

async function fetchAdventurers() {
  loading.value = true
  try {
    adventurers.value = await adventurersApi.list()
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

onMounted(fetchAdventurers)
</script>

<template>
  <div>
    <h1 class="mb-3">Adventurers</h1>

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
            <td>Day {{ entry.death_day }}</td>
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
            <td>Day {{ entry.bankruptcy_day }}</td>
          </tr>
        </tbody>
      </table>
    </template>

    <ModalDialog
      :is-open="showDetail"
      :title="selectedAdventurer?.name ?? 'Adventurer'"
      @close="showDetail = false"
    >
      <AdventurerDetail
        v-if="selectedAdventurer"
        :adventurer="selectedAdventurer"
        @close="showDetail = false"
        @level-up="onLevelUp"
      />
    </ModalDialog>
  </div>
</template>
