<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { ExpeditionSummary } from '../types'
import * as expeditionsApi from '../api/expeditions'
import { useGameTimeStore } from '../stores/gameTime'
import { useNotificationsStore } from '../stores/notifications'
import ExpeditionList from '../components/expeditions/ExpeditionList.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const router = useRouter()
const gameTime = useGameTimeStore()
const notifications = useNotificationsStore()

const expeditions = ref<ExpeditionSummary[]>([])
const loading = ref(false)
const activeTab = ref<'active' | 'completed'>('completed')

const activeExpeditions = computed(() =>
  expeditions.value.filter((e) => e.result === 'in_progress' || e.result === 'awaiting_choice')
)

const completedExpeditions = computed(() =>
  expeditions.value.filter((e) => e.result === 'completed').sort((a, b) => b.id - a.id)
)

async function fetchExpeditions() {
  loading.value = true
  expeditions.value = await expeditionsApi.list()
  loading.value = false
}

onMounted(fetchExpeditions)

function onSelectExpedition(id: number) {
  router.push(`/expedition/${id}/summary`)
}

async function onAdvanceDay() {
  await gameTime.advanceDay()
  await fetchExpeditions()
  notifications.add(`Advanced to day ${gameTime.currentDay}`, 'info')
}
</script>

<template>
  <div>
    <div class="flex flex-between">
      <h1>Expeditions</h1>
      <div class="flex gap-1">
        <button class="btn btn-primary" @click="router.push('/launch-expedition')">Launch Expedition</button>
        <button class="btn btn-secondary" @click="onAdvanceDay">Advance Day</button>
      </div>
    </div>

    <div class="filters-bar mb-2">
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
  </div>
</template>
