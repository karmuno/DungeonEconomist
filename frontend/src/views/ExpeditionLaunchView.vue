<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { PartyOut } from '../types'
import * as partiesApi from '../api/parties'
import * as expeditionsApi from '../api/expeditions'
import { useNotificationsStore } from '../stores/notifications'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const router = useRouter()
const route = useRoute()
const notifications = useNotificationsStore()

const party = ref<PartyOut | null>(null)
const dungeonLevel = ref(1)
const loading = ref(true)
const submitting = ref(false)

onMounted(async () => {
  const partyId = Number(route.params.partyId)
  if (partyId) {
    try {
      party.value = await partiesApi.getById(partyId)
    } catch {
      notifications.add('Party not found', 'error')
      router.push('/')
    }
  }
  loading.value = false
})

async function launchExpedition() {
  if (!party.value) return
  submitting.value = true
  try {
    await expeditionsApi.launch({
      party_id: party.value.id,
      dungeon_level: dungeonLevel.value,
      duration_days: 7,
    })
    notifications.add('Expedition launched!', 'success')
    router.push('/')
  } catch {
    notifications.add('Failed to launch expedition', 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="mb-3">Launch Expedition</h1>

    <LoadingSpinner v-if="loading" />
    <div v-else-if="!party" class="text-muted">No party selected</div>
    <div v-else class="card" style="max-width: 500px">
      <h3 class="mb-2">{{ party.name }}</h3>
      <p class="text-muted mb-2">{{ party.members.length }} members</p>

      <div class="mb-2">
        <div v-for="member in party.members" :key="member.id" class="mb-1">
          <strong>{{ member.name }}</strong>
          <span class="badge">{{ member.adventurer_class }}</span>
          <span class="text-muted">Lv {{ member.level }}</span>
        </div>
      </div>

      <div class="form-group mb-2">
        <label class="form-label">Dungeon Level: {{ dungeonLevel }}</label>
        <input v-model.number="dungeonLevel" type="range" min="1" max="6" class="form-input" />
      </div>

      <div class="form-group mb-3">
        <label class="form-label">Duration</label>
        <p class="text-muted">7 days (fixed)</p>
      </div>

      <div class="flex gap-1">
        <button
          class="btn btn-primary"
          :disabled="submitting"
          @click="launchExpedition"
        >
          Launch Expedition
        </button>
        <button
          class="btn btn-secondary"
          @click="router.push('/')"
        >
          Not Now
        </button>
      </div>
    </div>
  </div>
</template>
