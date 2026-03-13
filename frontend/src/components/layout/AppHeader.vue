<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '../../stores/player'
import { post } from '../../api/client'
import { useGameTimeStore } from '../../stores/gameTime'

const route = useRoute()
const router = useRouter()
const player = usePlayerStore()
const gameTime = useGameTimeStore()

const confirmingRestart = ref(false)
let restartTimeout: ReturnType<typeof setTimeout> | null = null

function handleRestart() {
  if (confirmingRestart.value) {
    confirmingRestart.value = false
    if (restartTimeout) clearTimeout(restartTimeout)
    doRestart()
  } else {
    confirmingRestart.value = true
    restartTimeout = setTimeout(() => {
      confirmingRestart.value = false
    }, 3000)
  }
}

async function doRestart() {
  await post('/game/new', {})
  await gameTime.fetchTime()
  await player.fetchPlayer()
  router.push({ name: 'new-game' })
}
</script>

<template>
  <header class="app-header">
    <router-link to="/" class="logo">{{ player.name || 'VentureKeep' }}</router-link>
    <nav>
      <router-link to="/" :class="{ active: route.path === '/' }">Dashboard</router-link>
      <router-link to="/adventurers" :class="{ active: route.path.startsWith('/adventurers') || route.path.startsWith('/form-party') }">Tavern</router-link>
      <router-link to="/parties" :class="{ active: route.path.startsWith('/parties') }">Parties</router-link>
      <router-link to="/expeditions" :class="{ active: route.path.startsWith('/expedition') }">Expeditions</router-link>
    </nav>
    <button
      class="restart-btn"
      :class="{ confirming: confirmingRestart }"
      @click="handleRestart"
    >
      {{ confirmingRestart ? 'Are you sure?' : 'Restart' }}
    </button>
  </header>
</template>

<style scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 56px;
  z-index: 100;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  padding: 0 24px;
  box-sizing: border-box;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-green);
  text-decoration: none;
  margin-right: auto;
  letter-spacing: 0.5px;
}

.logo:hover {
  text-decoration: none;
}

nav {
  display: flex;
  gap: 24px;
}

nav a {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  padding: 4px 0;
  transition: color 0.15s;
}

nav a:hover,
nav a.active {
  color: var(--accent-green);
  text-decoration: none;
}

.restart-btn {
  margin-left: 24px;
  padding: 4px 12px;
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-family: var(--font-mono);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.restart-btn:hover {
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.restart-btn.confirming {
  color: var(--accent-red, #e74c3c);
  border-color: var(--accent-red, #e74c3c);
}
</style>
