<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useGameTimeStore } from '../stores/gameTime'
import { usePlayerStore } from '../stores/player'
import * as keepsApi from '../api/keeps'
import type { KeepOut } from '../types'

const router = useRouter()
const auth = useAuthStore()
const gameTime = useGameTimeStore()
const player = usePlayerStore()

const keeps = ref<KeepOut[]>([])
const newKeepName = ref('')
const creating = ref(false)
const loading = ref(false)
const confirmDeleteId = ref<number | null>(null)
const deleteButtonRect = ref<{ top: number; right: number } | null>(null)

const confirmingKeep = computed(() => keeps.value.find(k => k.id === confirmDeleteId.value))

onMounted(async () => {
  try {
    keeps.value = await keepsApi.list()
  } finally {
    loading.value = false
  }

  document.addEventListener('keydown', handleEscapeKey)
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscapeKey)
  document.removeEventListener('click', handleOutsideClick)
})

function handleEscapeKey(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    confirmDeleteId.value = null
  }
}

function handleOutsideClick(e: MouseEvent) {
  const popover = document.querySelector('.delete-popover')
  if (popover && !popover.contains(e.target as Node)) {
    confirmDeleteId.value = null
  }
}

function openDeleteConfirm(e: MouseEvent, keepId: number) {
  e.stopPropagation()
  const button = e.currentTarget as HTMLElement
  const rect = button.getBoundingClientRect()
  const keepsCard = (button.closest('.keeps-card') || document.querySelector('.keeps-card')) as HTMLElement
  const cardRect = keepsCard.getBoundingClientRect()

  deleteButtonRect.value = {
    top: rect.bottom - cardRect.top + 8,
    right: cardRect.right - (rect.left + rect.width / 2) - 120,
  }
  confirmDeleteId.value = keepId
}

async function createKeep() {
  if (!newKeepName.value.trim()) return
  creating.value = true
  try {
    const keep = await keepsApi.create(newKeepName.value.trim())
    auth.selectKeep(keep)
    player.loadFromKeep()
    player.fetchPlayer()
    await gameTime.fetchTime()
    router.push('/form-party')
  } finally {
    creating.value = false
  }
}

async function selectKeep(keep: KeepOut) {
  auth.selectKeep(keep)
  player.loadFromKeep()
  player.fetchPlayer()
  await gameTime.fetchTime()
  router.push('/')
}

async function handleDelete(keep: KeepOut) {
  await keepsApi.deleteKeep(keep.id)
  keeps.value = keeps.value.filter(k => k.id !== keep.id)
  confirmDeleteId.value = null
}
</script>

<template>
  <div class="keeps-container">
    <div class="keeps-card card">
      <h1 class="mb-2">Your Keeps</h1>
      <p class="text-muted mb-3">
        Signed in as <strong>{{ auth.account?.username }}</strong>
        <span class="logout-link" @click="auth.logout(); router.push('/login')">(sign out)</span>
      </p>

      <div v-if="loading" class="text-muted">Loading...</div>

      <div v-else>
        <div v-if="keeps.length > 0" class="keep-list mb-3">
          <div
            v-for="keep in keeps"
            :key="keep.id"
            class="keep-item"
            @click="selectKeep(keep)"
          >
            <div class="keep-info">
              <div class="keep-name-row">
                <span class="keep-name">{{ keep.name }}</span>
                <span v-if="keep.dungeon_name" class="keep-vs">vs.</span>
                <span v-if="keep.dungeon_name" class="keep-dungeon">{{ keep.dungeon_name }}</span>
              </div>
              <div class="keep-meta">
                Day {{ keep.current_day }}
                &middot; {{ keep.treasury_gold }}gp
                <template v-if="keep.building_types.length">
                  &middot; {{ keep.building_types.join(', ') }}
                </template>
              </div>
            </div>
            <div class="keep-actions" @click.stop>
              <button
                class="delete-btn"
                title="Delete keep"
                @click="openDeleteConfirm($event, keep.id)"
              >
                Delete
              </button>
            </div>
          </div>
        </div>

        <div v-else class="text-muted mb-3">No keeps yet. Create one to start playing.</div>

        <form @submit.prevent="createKeep" class="create-form">
          <input
            v-model="newKeepName"
            class="form-input"
            type="text"
            placeholder="New keep name (e.g. The Dragon's Rest)"
          />
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="creating || !newKeepName.trim()"
          >
            {{ creating ? 'Creating...' : 'Create Keep' }}
          </button>
        </form>
      </div>

      <!-- Delete Confirm Popover -->
      <div v-if="confirmingKeep && deleteButtonRect" class="delete-popover-overlay" @click="confirmDeleteId = null" />
      <div
        v-if="confirmingKeep && deleteButtonRect"
        class="delete-popover"
        :style="{ top: deleteButtonRect.top + 'px', right: Math.max(0, deleteButtonRect.right) + 'px' }"
      >
        <div class="popover-title">
          Delete <span class="keep-name-red">{{ confirmingKeep.name }}</span>?
        </div>
        <div class="popover-body">
          This is permanent. All adventurers, parties, and progress in <strong>{{ confirmingKeep.name }}</strong> will be lost.
        </div>
        <div class="popover-actions">
          <button class="btn btn-secondary btn-sm" @click.stop="confirmDeleteId = null">Cancel</button>
          <button class="btn btn-danger btn-sm" @click.stop="handleDelete(confirmingKeep)">Delete Forever</button>
        </div>
        <div class="popover-arrow" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.keeps-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.keeps-card {
  max-width: 500px;
  width: 100%;
  text-align: center;
  position: relative;
}

.keeps-card h1 {
  color: var(--accent-green);
}

.logout-link {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 12px;
}

.logout-link:hover {
  color: var(--text-primary);
}

.keep-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
  max-height: 320px;
  overflow-y: auto;
}

.keep-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: border-color 0.15s;
}

.keep-item:hover {
  border-color: var(--accent-green);
}

.keep-name-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
}

.keep-name {
  font-weight: 700;
  color: var(--text-primary);
}

.keep-vs {
  font-size: 11px;
  font-style: italic;
  color: var(--text-muted);
}

.keep-dungeon {
  font-size: 13px;
  font-weight: 700;
  color: var(--accent-green);
}

.keep-meta {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  margin-top: 2px;
}

.keep-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.delete-btn {
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  padding: 3px 8px;
  font-family: inherit;
}

.delete-btn:hover {
  border-color: var(--accent-red);
  color: var(--accent-red);
}

.delete-popover-overlay {
  position: fixed;
  inset: 0;
  z-index: 10;
}

.delete-popover {
  position: absolute;
  z-index: 11;
  background: #111827;
  border: 1px solid var(--accent-red);
  border-radius: var(--radius);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
  padding: 12px;
  width: 260px;
}

.popover-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.keep-name-red {
  color: var(--accent-red);
}

.popover-body {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 10px;
}

.popover-body strong {
  color: var(--text-secondary);
}

.popover-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.popover-arrow {
  position: absolute;
  top: -6px;
  right: 115px;
  width: 10px;
  height: 10px;
  background: #111827;
  border-left: 1px solid var(--accent-red);
  border-top: 1px solid var(--accent-red);
  transform: rotate(45deg);
}

.create-form {
  display: flex;
  gap: 8px;
}

.create-form .form-input {
  flex: 1;
}
</style>
