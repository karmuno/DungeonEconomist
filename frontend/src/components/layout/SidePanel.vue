<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameTimeStore } from '../../stores/gameTime'
import { usePlayerStore } from '../../stores/player'
import { useNotificationsStore, type Notification } from '../../stores/notifications'
import { formatCurrency } from '../../utils/currency'
import { formatGameDay } from '../../utils/calendar'
import ModalDialog from '../shared/ModalDialog.vue'
import ExpeditionEventModal from '../expeditions/ExpeditionEventModal.vue'
import UpkeepDayModal from '../upkeep/UpkeepDayModal.vue'
import UpkeepForecastModal from '../upkeep/UpkeepForecastModal.vue'
import AdventurerSheetModal from '../adventurers/AdventurerSheetModal.vue'
import { formatCp } from '../../utils/currency'
import type { UpkeepDayData } from '../../types/upkeep'
import * as expeditionsApi from '../../api/expeditions'
import eventBus from '../../eventBus'

const router = useRouter()
const gameTime = useGameTimeStore()
const player = usePlayerStore()
const notifications = useNotificationsStore()

// Expedition choice popup
const showChoicePopup = ref(false)
const choiceMessage = ref('')
const choiceExpeditionId = ref<number | null>(null)
const choiceEventType = ref('')
const choosingInPopup = ref(false)

// Queue for multiple choices
interface PendingChoice {
  message: string;
  expeditionId: number;
  eventType: string;
}
const choiceQueue = ref<PendingChoice[]>([])

// Dashboard state must not refresh before the event that caused it is ON
// SCREEN. Once the popup appears the state may update — clicking out of an
// unresolved popup should show the current party state.
const pendingRefresh = ref(false)

function maybeFlushRefresh() {
  if (!pendingRefresh.value) return
  pendingRefresh.value = false
  // Bump the version (Dashboard, Tavern, Summary all watch it) now that the
  // event is visible
  gameTime.expeditionVersion++
}

function checkChoiceQueue() {
  if (showChoicePopup.value) return
  if (choiceQueue.value.length === 0) {
    maybeFlushRefresh()
    return
  }

  const next = choiceQueue.value.shift()!
  choiceMessage.value = next.message
  choiceExpeditionId.value = next.expeditionId
  choiceEventType.value = next.eventType
  showChoicePopup.value = true
  // The event is on screen — state may update now
  maybeFlushRefresh()
}


// Upkeep day modal — the treasury and roster must not update until Collect
const upkeepReport = ref<UpkeepDayData | null>(null)
const showUpkeepModal = ref(false)
const upkeepReopened = ref(false)
const pendingPlayerFetch = ref(false)
const showForecast = ref(false)
const sheetAdvId = ref<number | null>(null)

const shortRows = computed(() =>
  (player.upkeepForecast?.rows ?? []).filter(r => r.short_cp > 0)
)

function reopenUpkeep() {
  if (!upkeepReport.value) return
  upkeepReopened.value = true
  showUpkeepModal.value = true
}

function onUpkeepCollect() {
  showUpkeepModal.value = false
  if (upkeepReopened.value) return
  const d = upkeepReport.value
  if (d) {
    if (d.prison_names.length > 0) {
      const names = d.prison_names.length === 1
        ? d.prison_names[0]
        : `${d.prison_names.slice(0, -1).join(', ')} and ${d.prison_names[d.prison_names.length - 1]}`
      notifications.add(
        `${names} could not pay upkeep and ${d.prison_names.length === 1 ? 'was' : 'were'} sent to debtor's prison.`,
        { type: 'warning', action: { label: 'Upkeep', callback: reopenUpkeep } },
      )
    }
    notifications.add(
      `Upkeep collected: ${formatCp(d.collected_cp)} from ${d.collected_from} adventurer${d.collected_from === 1 ? '' : 's'}.`,
      { type: 'success', action: { label: 'Upkeep', callback: reopenUpkeep } },
    )
  }
  if (pendingPlayerFetch.value) {
    pendingPlayerFetch.value = false
    player.fetchPlayer()
    gameTime.expeditionVersion++
  }
}

// Level-up popup
const showLevelUpPopup = ref(false)
const levelUpMessage = ref('')

// Stairs discovered popup
const showStairsPopup = ref(false)
const stairsMessage = ref('')


function handleAction(notification: Notification) {
  if (notification.action?.callback) {
    notification.action.callback()
  } else if (notification.action?.route) {
    router.push(notification.action.route)
  }
  notifications.remove(notification.id)
}

const typeMap: Record<string, 'info' | 'success' | 'error' | 'warning'> = {
  recruitment: 'info',
  auto_start: 'info',
  loot: 'info',
  healing: 'success',
  expedition_complete: 'success',
  death: 'error',
  upkeep: 'warning',
  upkeep_deferred: 'warning',
  stairs: 'success',
  expedition_choice: 'warning',
  level_up: 'success',
}

function processEvents(events: Array<{ type: string; message: string; expedition_id?: number | null; first_time?: boolean; event_subtype?: string | null; data?: UpkeepDayData | null }>) {
  // On an upkeep day the ledger modal carries the whole story; its feed
  // lines are suppressed and recreated as clickable notifications on Collect
  const upkeepDay = events.some(e => e.type === 'upkeep' && e.data)
  for (const event of events) {
    if (event.type === 'upkeep' && upkeepDay) {
      if (event.data) {
        upkeepReport.value = event.data
        upkeepReopened.value = false
        showUpkeepModal.value = true
      }
      continue
    }
    // First-time level up — show popup
    if (event.type === 'level_up' && event.first_time) {
      levelUpMessage.value = event.message
      showLevelUpPopup.value = true
      continue
    }

    // Stairs discovered — ALWAYS show popup, no exceptions
    if (event.type === 'stairs_discovered') {
      stairsMessage.value = event.message
      showStairsPopup.value = true
      continue
    }

    // Expedition choice — queue it. No expeditionVersion bump here: state
    // must not refresh before the player has seen the queued event.
    if (event.type === 'expedition_choice' && event.expedition_id) {
      choiceQueue.value.push({
        message: event.message,
        expeditionId: event.expedition_id,
        eventType: event.event_subtype ?? '',
      })
      continue
    }

    const opts: Parameters<typeof notifications.add>[1] = {
      type: typeMap[event.type] ?? 'info',
    }
    if (event.type === 'expedition_complete' && event.expedition_id) {
      opts.action = {
        label: 'View Summary',
        route: `/expedition/${event.expedition_id}/summary`,
      }
    }
    notifications.add(event.message, opts)
  }
  
  // Try showing the first one in queue if nothing is showing
  checkChoiceQueue()
}

async function popupChoice(choice: string) {
  if (!choiceExpeditionId.value) return
  choosingInPopup.value = true
  try {
    const result = await expeditionsApi.choose(choiceExpeditionId.value, choice)

    // Route events through processEvents so stairs/level-ups get their popups
    if (result.events?.length) {
      processEvents(result.events)
    }

    if (result.status === 'next_event' && result.next_event) {
      // Show next event in same modal without advancing the day
      gameTime.expeditionVersion++
      choiceMessage.value = result.next_event.message
      choiceEventType.value = result.next_event.event_type
      choosingInPopup.value = false
      return
    } else if (result.status === 'in_progress') {
      // No more events this expedition — just close modal
      gameTime.expeditionVersion++
      showChoicePopup.value = false
      choosingInPopup.value = false
      checkChoiceQueue()
      return
    } else if (result.status === 'completed') {
      showChoicePopup.value = false
      await player.fetchPlayer()
      const retMsg = result.auto_choice === 'retreat'
        ? 'The party decided to retreat!'
        : result.retreated ? 'The party retreated safely' : 'The expedition is complete!'
      notifications.add(retMsg,
        {
          type: result.retreated ? 'info' : 'success',
          action: {
            label: 'View Summary',
            route: `/expedition/${choiceExpeditionId.value}/summary`,
          },
        },
      )
    } else {
      // Unknown status — close modal as fallback
      showChoicePopup.value = false
    }
    gameTime.expeditionVersion++
    choosingInPopup.value = false

    // Check if more choices are in queue
    checkChoiceQueue()
  } catch (e: any) {
    const detail = (e as any)?.data?.detail ?? 'Failed to submit choice'
    notifications.add(detail, 'error')
    showChoicePopup.value = false
    
    // Check if more choices are in queue even on error
    checkChoiceQueue()
  } finally {
    choosingInPopup.value = false
  }
}

async function viewExpedition() {
  showChoicePopup.value = false
  const wasTpk = choiceEventType.value === 'tpk'
  // If this was a TPK, auto-resolve the decision point so the expedition isn't stuck
  if (wasTpk && choiceExpeditionId.value) {
    try {
      const result = await expeditionsApi.choose(choiceExpeditionId.value, 'press_on')
      if (result.events?.length) processEvents(result.events)
      if (result.status === 'completed') await player.fetchPlayer()
      gameTime.expeditionVersion++
    } catch { /* expedition may already be resolved */ }
  }
  if (wasTpk) {
    // "Rest in Peace" returns to the dashboard, not the graveyard's summary
    router.push('/')
  } else if (choiceExpeditionId.value) {
    router.push(`/expedition/${choiceExpeditionId.value}/summary`)
  }
  // Check queue if they just closed the modal to navigate away
  // but they probably want to see the other popups later
  checkChoiceQueue()
}

const skipping = ref(false)

async function advanceDay() {
  try {
    const result = await gameTime.advanceDay()
    // Popups open in the same tick as the response — no awaits before them,
    // so nothing can render post-advance state ahead of the event popup
    notifications.onDayAdvanced(result.current_day)
    processEvents(result.events)
    pendingRefresh.value = true
    maybeFlushRefresh()
    if (showUpkeepModal.value) {
      pendingPlayerFetch.value = true
    } else {
      await player.fetchPlayer()
    }
  } catch {
    notifications.add('Failed to advance time', 'error')
  }
}

async function skipToEvent() {
  skipping.value = true
  try {
    const result = await gameTime.skipToEvent()
    notifications.onDayAdvanced(result.current_day)
    processEvents(result.events)
    pendingRefresh.value = true
    maybeFlushRefresh()
    if (showUpkeepModal.value) {
      pendingPlayerFetch.value = true
    } else {
      await player.fetchPlayer()
    }
  } catch (e) {
    notifications.add('Failed to skip time', 'error')
  } finally {
    skipping.value = false
  }
}

// Any popup closing may leave the queue drained — flush the held refresh
watch([showChoicePopup, showStairsPopup, showLevelUpPopup], () => {
  checkChoiceQueue()
  maybeFlushRefresh()
})

onMounted(() => {
  eventBus.on('game-events', processEvents)
})

onUnmounted(() => {
  eventBus.off('game-events', processEvents)
})
</script>

<template>
  <aside class="side-panel">
    <div class="panel-section">
      <h3 class="section-label">Game Day</h3>
      <div class="day-row">
        <div class="day-value">{{ gameTime.currentDay }}</div>
        <div class="day-calendar">{{ formatGameDay(gameTime.currentDay) }}</div>
      </div>
    </div>

    <div class="panel-section">
      <h3 class="section-label">Treasury</h3>
      <div class="treasury-value">{{ formatCurrency(player.treasuryGold, player.treasurySilver, player.treasuryCopper) }}</div>
      <div
        v-if="player.upkeepForecast && player.upkeepForecast.total_cp > 0"
        class="forecast-line"
        @click="showForecast = true"
      >
        <span class="forecast-amount">+{{ formatCp(player.upkeepForecast.total_cp) }}</span>
        <span class="forecast-when">upkeep · day {{ player.upkeepForecast.next_day }}</span>
      </div>
      <div v-if="shortRows.length > 0" class="at-risk" @click="showForecast = true">
        <div class="at-risk-head">
          {{ shortRows.length }} adventurer{{ shortRows.length === 1 ? '' : 's' }} cannot afford upkeep:
        </div>
        <div
          v-for="r in shortRows"
          :key="r.id"
          class="at-risk-name"
          @click.stop="sheetAdvId = r.id"
        >{{ r.name }}</div>
      </div>
    </div>

    <div class="time-controls">
      <button class="advance-btn" @click="advanceDay">Advance Day</button>
      <button class="skip-btn" :disabled="skipping" @click="skipToEvent">
        {{ skipping ? 'Skipping...' : 'Skip to Event' }}
      </button>
    </div>

    <div v-if="notifications.messages.length > 0" class="notif-header">
      <button class="clear-btn" @click="notifications.clear()">Clear</button>
    </div>
    <div v-if="notifications.messages.length > 0" class="notification-feed">
      <div
        v-for="notification in notifications.messages"
        :key="notification.id"
        class="notif"
        :class="notification.type"
      >
        <span class="notif-text">{{ notification.text }}</span>
        <span
          v-if="notification.action"
          class="notif-action"
          @click.stop="handleAction(notification)"
        >
          {{ notification.action.label }}
        </span>
        <button
          class="notif-dismiss"
          @click.stop="notifications.remove(notification.id)"
        >
          &times;
        </button>
      </div>
    </div>
  </aside>

  <!-- Expedition Event Modal -->
  <ExpeditionEventModal
    :is-open="showChoicePopup"
    :expedition-id="choiceExpeditionId"
    :event-message="choiceMessage"
    :event-type="choiceEventType"
    :choosing="choosingInPopup"
    @choose="popupChoice"
    @close="viewExpedition"
  />

  <UpkeepDayModal
    :is-open="showUpkeepModal"
    :data="upkeepReport"
    :reopened="upkeepReopened"
    @collect="onUpkeepCollect"
    @open-sheet="sheetAdvId = $event"
  />

  <UpkeepForecastModal
    :is-open="showForecast"
    :forecast="player.upkeepForecast"
    @close="showForecast = false"
    @open-sheet="sheetAdvId = $event"
  />

  <AdventurerSheetModal :adventurer-id="sheetAdvId" @close="sheetAdvId = null" />

  <!-- Level-Up Popup -->
  <ModalDialog
    :is-open="showLevelUpPopup"
    title="Level Up!"
    @close="showLevelUpPopup = false"
  >
    <div class="choice-popup">
      <p class="choice-popup-msg">{{ levelUpMessage }}</p>
      <div class="choice-popup-buttons">
        <button
          class="btn btn-primary"
          @click="showLevelUpPopup = false"
        >
          Awesome!
        </button>
      </div>
    </div>
  </ModalDialog>

  <!-- Stairs Discovered Popup -->
  <ModalDialog
    :is-open="showStairsPopup"
    title="Stairs Discovered!"
    @close="showStairsPopup = false"
  >
    <div class="choice-popup">
      <p class="choice-popup-msg">{{ stairsMessage }}</p>
      <div class="choice-popup-buttons">
        <button
          class="btn btn-success"
          @click="showStairsPopup = false"
        >
          Excellent!
        </button>
      </div>
    </div>
  </ModalDialog>
</template>

<style scoped>
.side-panel {
  position: fixed;
  left: 0;
  top: 56px;
  width: 260px;
  height: calc(100vh - 56px);
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  padding: 14px 16px;
  box-sizing: border-box;
  overflow-y: auto;
}

.panel-section {
  margin-bottom: 12px;
}

.section-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-muted);
  margin: 0 0 2px;
}

.day-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.day-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.day-calendar {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.panel-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.panel-stat {
  flex: 1;
}

.treasury-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--accent-green);
}

.score-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.time-controls {
  display: flex;
  gap: 6px;
}

.advance-btn {
  flex: 1;
  padding: 8px 12px;
  background: var(--accent-green-dark);
  color: #000;
  border: none;
  border-radius: var(--border-radius);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.15s;
}

.advance-btn:hover {
  background: var(--accent-green);
}

.skip-btn {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg-secondary);
  color: var(--text-muted);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s, color 0.15s;
}

.skip-btn:hover:not(:disabled) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.skip-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notif-header {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.clear-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 11px;
  cursor: pointer;
  padding: 0;
}

.clear-btn:hover {
  color: var(--text-primary);
}

.notification-feed {
  margin-top: 4px;
  max-height: calc(100vh - 310px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.notif {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  padding: 4px 6px;
  border-radius: var(--border-radius);
  font-size: 10px;
  line-height: 1.3;
  border: 1px solid transparent;
  background: var(--bg-secondary);
  color: var(--text-muted);
}

.notif.success {
  background-color: #052e16;
  border-color: var(--accent-green-dim);
  color: var(--accent-green);
}

.notif.error {
  background-color: #450a0a;
  border-color: #7f1d1d;
  color: var(--accent-red);
}

.notif.info {
  background-color: #0c1929;
  border-color: #1e3a5f;
  color: var(--accent-blue);
}

.notif.warning {
  background-color: #422006;
  border-color: #78350f;
  color: #fbbf24;
}

.notif-text {
  flex: 1;
  word-break: break-word;
}

.notif-action {
  cursor: pointer;
  text-decoration: underline;
  font-weight: 600;
  white-space: nowrap;
  opacity: 0.9;
}

.notif-action:hover {
  opacity: 1;
}

.notif-dismiss {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.6;
  padding: 0;
  line-height: 1;
  flex-shrink: 0;
}

.notif-dismiss:hover {
  opacity: 1;
}

/* Choice popup */
.choice-popup {
  text-align: center;
  padding: 0.5rem 0;
}

.choice-popup-msg {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 1rem;
}

.choice-popup-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-bottom: 0.75rem;
}

.choice-popup-buttons .btn {
  min-width: 120px;
}


.forecast-line {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 2px;
  cursor: pointer;
}

.forecast-amount {
  font-size: 11px;
  color: #4ade80;
  text-decoration: underline;
  text-decoration-color: #374151;
  text-underline-offset: 2px;
}

.forecast-line:hover .forecast-amount {
  text-decoration-color: #4ade80;
}

.forecast-when {
  font-size: 10px;
  color: #6b7280;
}

.at-risk {
  display: flex;
  flex-direction: column;
  gap: 1px;
  margin-top: 4px;
  cursor: pointer;
}

.at-risk-head {
  font-size: 10px;
  color: #ef4444;
}

.at-risk-name {
  font-size: 10px;
  color: #ef4444;
  padding-left: 8px;
  text-decoration: underline;
  text-decoration-color: rgba(239, 68, 68, 0.3);
  text-underline-offset: 2px;
}

.at-risk-name:hover {
  text-decoration-color: #ef4444;
}
</style>
