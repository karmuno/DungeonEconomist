<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

onMounted(async () => {
  try {
    keeps.value = await keepsApi.list()
  } finally {
    loading.value = false
  }
})

async function createKeep() {
  if (!newKeepName.value.trim()) return
  creating.value = true
  try {
    const keep = await keepsApi.create(newKeepName.value.trim())
    auth.selectKeep(keep)
    player.fetchPlayer()
    await gameTime.fetchTime()
    router.push('/form-party')
  } finally {
    creating.value = false
  }
}

async function selectKeep(keep: KeepOut) {
  auth.selectKeep(keep)
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
            :class="{ 'keep-item-confirming': confirmDeleteId === keep.id }"
            @click="confirmDeleteId === keep.id ? null : selectKeep(keep)"
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
              <template v-if="confirmDeleteId === keep.id">
                <span class="delete-warning">This is permanent.</span>
                <button class="btn-delete-confirm" @click="handleDelete(keep)">Delete Forever</button>
                <button class="btn-delete-cancel" @click="confirmDeleteId = null">Cancel</button>
              </template>
              <button
                v-else
                class="delete-btn"
                title="Delete keep"
                @click="confirmDeleteId = keep.id"
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
  border-radius: var(--border-radius);
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
  font-weight: 700;
  color: var(--accent-red, #e74c3c);
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

.keep-item-confirming {
  border-color: var(--accent-red, #e74c3c);
  cursor: default;
}

.delete-warning {
  font-size: 11px;
  color: var(--accent-red, #e74c3c);
  white-space: nowrap;
}

.delete-btn {
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  padding: 3px 8px;
}

.delete-btn:hover {
  border-color: var(--accent-red, #e74c3c);
  color: var(--accent-red, #e74c3c);
}

.btn-delete-confirm {
  background: var(--accent-red, #e74c3c);
  border: none;
  border-radius: var(--border-radius);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  padding: 4px 10px;
  white-space: nowrap;
}

.btn-delete-confirm:hover {
  opacity: 0.85;
}

.btn-delete-cancel {
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  padding: 3px 8px;
}

.btn-delete-cancel:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}

.create-form {
  display: flex;
  gap: 8px;
}

.create-form .form-input {
  flex: 1;
}
</style>
