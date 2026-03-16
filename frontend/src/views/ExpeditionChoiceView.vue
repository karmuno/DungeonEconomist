<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as expeditionsApi from '../api/expeditions'
import type { PendingEvent } from '../api/expeditions'
import { useNotificationsStore } from '../stores/notifications'
import { usePlayerStore } from '../stores/player'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const router = useRouter()
const route = useRoute()
const notifications = useNotificationsStore()
const player = usePlayerStore()

const loading = ref(true)
const submitting = ref(false)
const partyName = ref('')
const pendingEvent = ref<PendingEvent | null>(null)
const expeditionId = ref(0)

onMounted(async () => {
  expeditionId.value = Number(route.params.id)
  try {
    const data = await expeditionsApi.getPending(expeditionId.value)
    if (!data.pending) {
      router.push('/')
      return
    }
    partyName.value = data.party_name ?? 'Unknown'
    pendingEvent.value = data.pending_event ?? null
  } catch {
    notifications.add('Failed to load expedition event', 'error')
    router.push('/')
  }
  loading.value = false
})

async function makeChoice(choice: string) {
  submitting.value = true
  try {
    const result = await expeditionsApi.choose(expeditionId.value, choice)

    // Process any events from the resolution
    for (const evt of result.events ?? []) {
      const typeMap: Record<string, string> = {
        death: 'error', loot: 'info', stairs: 'success',
        upkeep: 'warning', expedition_complete: 'success',
      }
      notifications.add(evt.message, { type: (typeMap[evt.type] ?? 'info') as any })
    }

    if (result.status === 'awaiting_choice' && result.pending_event) {
      // Another decision point — update the view
      pendingEvent.value = result.pending_event
      submitting.value = false
    } else {
      // Expedition complete
      await player.fetchPlayer()
      if (result.retreated) {
        notifications.add(`${partyName.value} retreated safely`, 'info')
      } else {
        notifications.add(`${partyName.value} completed the expedition!`, 'success')
      }
      router.push('/')
    }
  } catch {
    notifications.add('Failed to submit choice', 'error')
    submitting.value = false
  }
}

function eventIcon(type: string): string {
  switch (type) {
    case 'death': return '\u2620'      // skull
    case 'big_haul': return '\uD83D\uDCB0'  // money bag
    case 'stairs': return '\uD83E\uDDED'     // compass/map
    default: return '\u2757'
  }
}

function eventClass(type: string): string {
  switch (type) {
    case 'death': return 'event-death'
    case 'big_haul': return 'event-haul'
    case 'stairs': return 'event-stairs'
    default: return ''
  }
}
</script>

<template>
  <div>
    <h1>Expedition Event</h1>

    <LoadingSpinner v-if="loading" />
    <div v-else-if="pendingEvent" class="choice-container">
      <div class="choice-card card" :class="eventClass(pendingEvent.type)">
        <div class="event-icon">{{ eventIcon(pendingEvent.type) }}</div>
        <h2 class="event-party">{{ partyName }}</h2>
        <p class="event-message">{{ pendingEvent.message }}</p>

        <div v-if="pendingEvent.loot_so_far" class="event-detail">
          Loot secured so far: {{ pendingEvent.loot_so_far }} gp
        </div>

        <div class="choice-buttons">
          <button
            class="btn btn-primary choice-btn"
            :disabled="submitting"
            @click="makeChoice('press_on')"
          >
            Press On
          </button>
          <button
            class="btn btn-secondary choice-btn"
            :disabled="submitting"
            @click="makeChoice('retreat')"
          >
            Retreat
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.choice-container {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.choice-card {
  max-width: 500px;
  width: 100%;
  text-align: center;
  padding: 2rem;
}

.event-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.event-party {
  color: var(--text-primary);
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.event-message {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 1rem;
}

.event-detail {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--accent-green);
  margin-bottom: 1rem;
}

.choice-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.choice-btn {
  min-width: 140px;
  padding: 10px 24px;
  font-size: 14px;
}

/* Event type accents */
.event-death {
  border-color: var(--accent-red, #e74c3c);
}

.event-haul {
  border-color: #fbbf24;
}

.event-stairs {
  border-color: var(--accent-green);
}
</style>
