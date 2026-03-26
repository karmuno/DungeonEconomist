<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '../../stores/player'
import { useAuthStore } from '../../stores/auth'
import { useNotificationsStore } from '../../stores/notifications'
import eventBus from '../../eventBus'

const route = useRoute()
const router = useRouter()
const player = usePlayerStore()
const auth = useAuthStore()
const notifications = useNotificationsStore()

const showMetricsBtn = ref(false)

function toggleMetricsButton() {
  showMetricsBtn.value = !showMetricsBtn.value
}

function openMetrics() {
  eventBus.emit('toggle-metrics')
}

onMounted(() => eventBus.on('toggle-metrics-button', toggleMetricsButton))
onUnmounted(() => eventBus.off('toggle-metrics-button', toggleMetricsButton))

function switchKeep() {
  auth.clearKeep()
  notifications.clear()
  router.push({ name: 'keeps' })
}

function logout() {
  auth.logout()
  notifications.clear()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="app-header">
    <router-link to="/" class="logo">VentureKeep</router-link>
    <nav>
      <router-link to="/" :class="{ active: route.path === '/' }">{{ player.name || 'Keep' }}</router-link>
      <router-link to="/village" :class="{ active: route.path === '/village' }">Village</router-link>
      <router-link to="/adventurers" :class="{ active: route.path.startsWith('/adventurers') || route.path.startsWith('/form-party') }">Tavern</router-link>
      <router-link to="/parties" :class="{ active: route.path.startsWith('/parties') }">Parties</router-link>
      <router-link to="/expeditions" :class="{ active: route.path.startsWith('/expedition') }">Expeditions</router-link>
    </nav>
    <div class="header-actions">
      <button v-if="showMetricsBtn" class="header-btn metrics-btn" @click="openMetrics">Metrics</button>
      <button class="header-btn" @click="switchKeep">Switch Keep</button>
      <button class="header-btn" @click="logout">Sign Out</button>
    </div>
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

.header-actions {
  display: flex;
  gap: 8px;
  margin-left: 24px;
}

.header-btn {
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

.header-btn:hover {
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.metrics-btn {
  color: #a78bfa;
  border-color: #a78bfa44;
}

.metrics-btn:hover {
  color: #c4b5fd;
  border-color: #a78bfa;
}
</style>
