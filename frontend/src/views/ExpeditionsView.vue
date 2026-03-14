<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { ExpeditionSummary } from '../types'
import * as expeditionsApi from '../api/expeditions'
import { useGameTimeStore } from '../stores/gameTime'
import { useNotificationsStore } from '../stores/notifications'
import ExpeditionList from '../components/expeditions/ExpeditionList.vue'
import ExpeditionLaunchForm from '../components/expeditions/ExpeditionLaunchForm.vue'
import ModalDialog from '../components/shared/ModalDialog.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const gameTime = useGameTimeStore()
const notifications = useNotificationsStore()

const expeditions = ref<ExpeditionSummary[]>([])
const loading = ref(false)
const activeTab = ref<'active' | 'completed'>('active')
const showLaunch = ref(false)

const preselectedPartyId = computed(() => {
  const id = route.query.partyId
  return id ? Number(id) : undefined
})

const activeExpeditions = computed(() =>
  expeditions.value.filter((e) => e.result === 'in_progress')
)

const completedExpeditions = computed(() =>
  expeditions.value.filter((e) => e.result !== 'in_progress')
)

async function fetchExpeditions() {
  loading.value = true
  expeditions.value = await expeditionsApi.list()
  loading.value = false
}

onMounted(async () => {
  await fetchExpeditions()
  if (preselectedPartyId.value) {
    showLaunch.value = true
  }
})

function onSelectExpedition(id: number) {
  router.push(`/expedition/${id}/summary`)
}

async function onLaunched() {
  showLaunch.value = false
  await fetchExpeditions()
  notifications.add('Expedition launched!', 'success')
}

async function onAdvanceDay() {
  await gameTime.advanceDay()
  await fetchExpeditions()
  notifications.add(`Advanced to day ${gameTime.currentDay}`, 'info')
}
</script>

<template>
  <div>
    <div class="flex flex-between mb-3">
      <h1>Expeditions</h1>
      <div class="flex gap-1">
        <button class="btn btn-primary" @click="showLaunch = true">Launch Expedition</button>
        <button class="btn btn-secondary" @click="onAdvanceDay">Advance Day</button>
      </div>
    </div>

    <div class="filters-bar mb-3">
      <button
        class="btn btn-sm"
        :class="activeTab === 'active' ? 'btn-primary' : 'btn-secondary'"
        @click="activeTab = 'active'"
      >
        Active
      </button>
      <button
        class="btn btn-sm"
        :class="activeTab === 'completed' ? 'btn-primary' : 'btn-secondary'"
        @click="activeTab = 'completed'"
      >
        Completed
      </button>
    </div>

    <LoadingSpinner v-if="loading" message="Loading expeditions..." />

    <template v-else>
      <ExpeditionList
        v-if="activeTab === 'active'"
        :expeditions="activeExpeditions"
        @select="onSelectExpedition"
      />
      <ExpeditionList
        v-else
        :expeditions="completedExpeditions"
        @select="onSelectExpedition"
      />
    </template>

    <ModalDialog :is-open="showLaunch" title="Launch Expedition" @close="showLaunch = false">
      <ExpeditionLaunchForm
        :preselected-party-id="preselectedPartyId"
        @launched="onLaunched"
        @cancel="showLaunch = false"
      />
    </ModalDialog>

  </div>
</template>
