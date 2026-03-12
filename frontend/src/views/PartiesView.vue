<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { PartyOut } from '../types'
import * as partiesApi from '../api/parties'
import { useNotificationsStore } from '../stores/notifications'
import PartyCard from '../components/parties/PartyCard.vue'
import PartyForm from '../components/parties/PartyForm.vue'
import PartyMemberManager from '../components/parties/PartyMemberManager.vue'
import PartySupplyManager from '../components/parties/PartySupplyManager.vue'
import PartyFundsForm from '../components/parties/PartyFundsForm.vue'
import ModalDialog from '../components/shared/ModalDialog.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import EmptyState from '../components/shared/EmptyState.vue'

const notifications = useNotificationsStore()

const parties = ref<PartyOut[]>([])
const loading = ref(false)
const showCreate = ref(false)
const showEdit = ref(false)
const showMembers = ref(false)
const showSupplies = ref(false)
const showFunds = ref(false)
const selectedParty = ref<PartyOut | null>(null)

async function fetchParties() {
  loading.value = true
  parties.value = await partiesApi.list()
  loading.value = false
}

onMounted(fetchParties)

function openEdit(party: PartyOut) {
  selectedParty.value = party
  showEdit.value = true
}

function openMembers(party: PartyOut) {
  selectedParty.value = party
  showMembers.value = true
}

function openSupplies(party: PartyOut) {
  selectedParty.value = party
  showSupplies.value = true
}

function openFunds(party: PartyOut) {
  selectedParty.value = party
  showFunds.value = true
}

async function onSaved() {
  showCreate.value = false
  showEdit.value = false
  await fetchParties()
  notifications.add('Party saved', 'success')
}

async function onMembersUpdated() {
  await refreshSelectedParty()
  await fetchParties()
  notifications.add('Party members updated', 'success')
}

async function onSuppliesUpdated() {
  await refreshSelectedParty()
  await fetchParties()
  notifications.add('Party supplies updated', 'success')
}

async function onFundsUpdated() {
  showFunds.value = false
  await fetchParties()
  notifications.add('Party funds updated', 'success')
}

async function refreshSelectedParty() {
  if (selectedParty.value) {
    selectedParty.value = await partiesApi.getById(selectedParty.value.id)
  }
}
</script>

<template>
  <div>
    <div class="flex flex-between mb-3">
      <h1>Parties</h1>
      <button class="btn btn-primary" @click="showCreate = true">New Party</button>
    </div>

    <LoadingSpinner v-if="loading" message="Loading parties..." />

    <div v-else-if="parties.length === 0">
      <EmptyState message="No parties yet. Create one to get started!" />
    </div>

    <div v-else class="stats-grid">
      <PartyCard
        v-for="party in parties"
        :key="party.id"
        :party="party"
        @select="openEdit(party)"
        @manage="openMembers(party)"
        @launch="$router.push({ name: 'expeditions', query: { partyId: party.id } })"
      />
    </div>

    <ModalDialog :is-open="showCreate" title="Create Party" @close="showCreate = false">
      <PartyForm @saved="onSaved" @cancel="showCreate = false" />
    </ModalDialog>

    <ModalDialog :is-open="showEdit" title="Edit Party" @close="showEdit = false">
      <PartyForm v-if="selectedParty" :party="selectedParty" @saved="onSaved" @cancel="showEdit = false" />
    </ModalDialog>

    <ModalDialog :is-open="showMembers" title="Manage Members" @close="showMembers = false">
      <template v-if="selectedParty">
        <PartyMemberManager :party="selectedParty" @updated="onMembersUpdated" />
        <div class="mt-2">
          <button class="btn btn-secondary btn-sm" @click="openSupplies(selectedParty!)">Manage Supplies</button>
          <button class="btn btn-secondary btn-sm" @click="openFunds(selectedParty!)">Manage Funds</button>
        </div>
      </template>
    </ModalDialog>

    <ModalDialog :is-open="showSupplies" title="Manage Supplies" @close="showSupplies = false">
      <PartySupplyManager v-if="selectedParty" :party="selectedParty" @updated="onSuppliesUpdated" />
    </ModalDialog>

    <ModalDialog :is-open="showFunds" title="Manage Funds" @close="showFunds = false">
      <PartyFundsForm v-if="selectedParty" :party="selectedParty" @updated="onFundsUpdated" @cancel="showFunds = false" />
    </ModalDialog>
  </div>
</template>
