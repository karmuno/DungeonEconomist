<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { post } from '../../api/client'
import { useAuthStore } from '../../stores/auth'
import { usePlayerStore } from '../../stores/player'
import eventBus from '../../eventBus'

const auth = useAuthStore()
const player = usePlayerStore()

const isOpen = ref(false)
const input = ref('')
const history = ref<Array<{ cmd: string; result: string; error: boolean }>>([])
const inputEl = ref<HTMLInputElement | null>(null)
const submitting = ref(false)

function toggle() {
  if (!auth.account?.is_admin) return
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => inputEl.value?.focus())
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.ctrlKey && e.key === '/') {
    e.preventDefault()
    toggle()
  }
  if (e.key === 'Escape' && isOpen.value) {
    isOpen.value = false
  }
}

async function execute() {
  const cmd = input.value.trim()
  if (!cmd || submitting.value) return
  input.value = ''

  // Client-side commands
  if (cmd === 'metrics') {
    history.value.push({ cmd, result: 'Metrics button toggled in header.', error: false })
    eventBus.emit('toggle-metrics-button')
    nextTick(() => inputEl.value?.focus())
    return
  }

  submitting.value = true

  try {
    const result = await post<{ ok: boolean; message: string; events?: any[] }>('/admin/exec', { command: cmd })
    history.value.push({ cmd, result: result.message, error: false })

    if (result.events && result.events.length > 0) {
      eventBus.emit('game-events', result.events)
    }
    eventBus.emit('refresh-dashboard')

    // Refresh treasury display
    await player.fetchPlayer()
  } catch (e: any) {
    const detail = e?.data?.detail ?? e?.message ?? 'Unknown error'
    history.value.push({ cmd, result: detail, error: true })
  } finally {
    submitting.value = false
    nextTick(() => inputEl.value?.focus())
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="console-overlay" @click.self="isOpen = false">
      <div class="console-panel">
        <div class="console-header">
          <span class="console-title">Admin Console</span>
          <button class="console-close" @click="isOpen = false">&times;</button>
        </div>
        <div class="console-history">
          <div v-for="(entry, i) in history" :key="i" class="console-entry">
            <div class="console-cmd">&gt; {{ entry.cmd }}</div>
            <div class="console-result" :class="{ error: entry.error }">{{ entry.result }}</div>
          </div>
        </div>
        <form class="console-input-row" @submit.prevent="execute">
          <span class="console-prompt">&gt;</span>
          <input
            ref="inputEl"
            v-model="input"
            class="console-input"
            type="text"
            placeholder="add gp 30"
            autocomplete="off"
            spellcheck="false"
            :disabled="submitting"
          />
        </form>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.console-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  justify-content: center;
  padding-top: 80px;
}

.console-panel {
  width: 560px;
  max-height: 400px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7);
  font-family: var(--font-mono);
  font-size: 13px;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #222;
}

.console-title {
  color: #fbbf24;
  font-weight: 700;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.console-close {
  background: none;
  border: none;
  color: #666;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.console-close:hover {
  color: #fff;
}

.console-history {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
  min-height: 60px;
}

.console-entry {
  margin-bottom: 6px;
}

.console-cmd {
  color: #888;
}

.console-result {
  color: var(--accent-green, #4ade80);
  padding-left: 12px;
}

.console-result.error {
  color: #e74c3c;
}

.console-input-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border-top: 1px solid #222;
}

.console-prompt {
  color: #fbbf24;
  font-weight: 700;
}

.console-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #fff;
  font-family: var(--font-mono);
  font-size: 13px;
}

.console-input::placeholder {
  color: #444;
}
</style>
