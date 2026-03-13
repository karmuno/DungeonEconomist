<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { post } from '../api/client'
import { useGameTimeStore } from '../stores/gameTime'
import { usePlayerStore } from '../stores/player'

const router = useRouter()
const gameTime = useGameTimeStore()
const player = usePlayerStore()

const keepName = ref('')
const submitting = ref(false)

async function createKeep() {
  if (!keepName.value.trim()) return
  submitting.value = true
  try {
    await post('/game/new', { keep_name: keepName.value.trim() })
    await gameTime.fetchTime()
    await player.fetchPlayer()
    router.push('/form-party')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="new-game-container">
    <div class="new-game-card card">
      <h1 class="mb-2">VentureKeep</h1>
      <p class="text-muted mb-3">Name your adventurer's keep to begin.</p>
      <form @submit.prevent="createKeep">
        <div class="form-group mb-3">
          <label class="form-label">Keep Name</label>
          <input
            v-model="keepName"
            class="form-input"
            type="text"
            placeholder="e.g. The Dragon's Rest"
            autofocus
            required
          />
        </div>
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="submitting || !keepName.trim()"
          style="width: 100%"
        >
          Create Keep
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.new-game-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.new-game-card {
  max-width: 400px;
  width: 100%;
  text-align: center;
}

.new-game-card h1 {
  color: var(--accent-green);
}
</style>
