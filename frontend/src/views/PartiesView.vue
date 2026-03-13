<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { PartyOut } from '../types'
import * as partiesApi from '../api/parties'
import { useNotificationsStore } from '../stores/notifications'
import PartyCard from '../components/parties/PartyCard.vue'
import PartyForm from '../components/parties/PartyForm.vue'
import PartyMemberManager from '../components/parties/PartyMemberManager.vue'
import ModalDialog from '../components/shared/ModalDialog.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import EmptyState from '../components/shared/EmptyState.vue'

const notifications = useNotificationsStore()

const parties = ref<PartyOut[]>([])
const loading = ref(false)
const showCreate = ref(false)
const showEdit = ref(false)
const showMembers = ref(false)
const selectedParty = ref<PartyOut | null>(null)
// Track newly created party so we can open member manager right away
const newPartyId = ref<number | null>(null)

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

async function onSaved(party?: PartyOut) {
  showCreate.value = false
  showEdit.value = false
  await fetchParties()
  notifications.add('Party saved', 'success')

  // If we just created a new party, open member manager
  if (party && newPartyId.value === null && !showEdit.value) {
    newPartyId.value = party.id
    selectedParty.value = await partiesApi.getById(party.id)
    showMembers.value = true
  }
}

async function onMembersUpdated() {
  await refreshSelectedParty()
  await fetchParties()
  notifications.add('Party members updated', 'success')
}

async function refreshSelectedParty() {
  if (selectedParty.value) {
    selectedParty.value = await partiesApi.getById(selectedParty.value.id)
  }
}

function onMembersClose() {
  showMembers.value = false
  newPartyId.value = null
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

    <ModalDialog :is-open="showMembers" title="Manage Members" @close="onMembersClose">
      <template v-if="selectedParty">
        <PartyMemberManager :party="selectedParty" @updated="onMembersUpdated" />
      </template>
    </ModalDialog>
  </div>
</template>
