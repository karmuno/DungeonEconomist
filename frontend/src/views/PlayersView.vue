<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { PlayerOut } from '../types'
import * as playersApi from '../api/players'
import { useNotificationsStore } from '../stores/notifications'
import PlayerList from '../components/players/PlayerList.vue'
import PlayerForm from '../components/players/PlayerForm.vue'
import ModalDialog from '../components/shared/ModalDialog.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const notifications = useNotificationsStore()

const players = ref<PlayerOut[]>([])
const loading = ref(false)
const showCreate = ref(false)

async function fetchPlayers() {
  loading.value = true
  players.value = await playersApi.list()
  loading.value = false
}

onMounted(fetchPlayers)

async function onCreated() {
  showCreate.value = false
  await fetchPlayers()
  notifications.add('Player created', 'success')
}
</script>

<template>
  <div>
    <div class="flex flex-between mb-3">
      <h1>Players</h1>
      <button class="btn btn-primary" @click="showCreate = true">New Player</button>
    </div>

    <LoadingSpinner v-if="loading" message="Loading players..." />
    <PlayerList v-else :players="players" />

    <ModalDialog :is-open="showCreate" title="Create Player" @close="showCreate = false">
      <PlayerForm @created="onCreated" @cancel="showCreate = false" />
    </ModalDialog>
  </div>
</template>
