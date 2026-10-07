<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as expeditionsApi from '../api/expeditions'
import type { ExpeditionMemberResult, PendingEvent } from '../api/expeditions'
import { useNotificationsStore } from '../stores/notifications'
import { usePlayerStore } from '../stores/player'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import LinkedText from '../components/adventurers/LinkedText.vue'
import AdventurerSheetModal from '../components/adventurers/AdventurerSheetModal.vue'
import eventBus from '../eventBus'

const router = useRouter()
const route = useRoute()
const notifications = useNotificationsStore()
const player = usePlayerStore()

const loading = ref(true)
const submitting = ref(false)
const partyName = ref('')
const pendingEvent = ref<PendingEvent | null>(null)
const expeditionId = ref(0)
const members = ref<ExpeditionMemberResult[]>([])
const sheetAdvId = ref<number | null>(null)

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
    // The party, so the decision can be made with their sheets in reach
    try {
      members.value = (await expeditionsApi.getSummary(expeditionId.value)).member_results
    } catch {
      members.value = []
    }
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

    // Hand these to the side panel: it owns the level-up and stairs popups
    // and turns every adventurer name into a link to their sheet
    if (result.events?.length) eventBus.emit('game-events', result.events)

    if (result.status === 'in_progress') {
      // Expedition continues — back to dashboard
      notifications.add(`${partyName.value} presses on...`, 'info')
      router.push('/')
    } else if (result.status === 'completed') {
      await player.fetchPlayer()
      if (result.retreated) {
        notifications.add(`${partyName.value} retreated safely`, 'info')
      } else {
        notifications.add(`${partyName.value} completed the expedition!`, 'success')
      }
      router.push('/')
    } else {
      submitting.value = false
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
        <p class="event-message"><LinkedText :text="pendingEvent.message" :refs="members" @open="sheetAdvId = $event" /></p>

        <div v-if="members.length" class="event-party">
          <div v-for="m in members" :key="m.id" class="event-member" :class="{ 'adv-dead': !m.alive }">
            <span class="adv-link" @click="sheetAdvId = m.id">{{ m.name }}</span>
            <span class="member-meta">{{ m.adventurer_class }} · Lv {{ m.level }} · {{ m.alive ? `${m.hp_current}/${m.hp_max} HP` : 'Dead' }}</span>
          </div>
        </div>

        <div v-if="pendingEvent.loot_so_far" class="event-detail">
          Loot secured so far: {{ pendingEvent.loot_so_far }} gp
        </div>

        <div class="choice-buttons">
          <template v-if="pendingEvent.type === 'stairs'">
            <button
              class="btn btn-primary choice-btn"
              :disabled="submitting"
              @click="makeChoice('press_on_same')"
            >
              Continue This Level
            </button>
            <button
              class="btn btn-success choice-btn"
              :disabled="submitting"
              @click="makeChoice('press_on_next')"
            >
              Descend Deeper
            </button>
            <button
              class="btn btn-secondary choice-btn"
              :disabled="submitting"
              @click="makeChoice('retreat')"
            >
              Retreat (Level Saved)
            </button>
          </template>
          <template v-else>
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
          </template>
        </div>
      </div>
    </div>
  </div>
  <AdventurerSheetModal :adventurer-id="sheetAdvId" @close="sheetAdvId = null" />
</template>

<style scoped>
.event-party {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 12px 0;
  text-align: left;
}

.event-member {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 12px;
}

.event-member.adv-dead {
  color: #6b7280;
}

.member-meta {
  font-size: 11px;
  color: #6b7280;
}

.adv-link {
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: #374151;
  text-underline-offset: 2px;
}

.adv-link:hover {
  color: #4ade80;
  text-decoration-color: #4ade80;
}

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
