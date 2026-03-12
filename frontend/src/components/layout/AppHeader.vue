<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <header class="app-header">
    <router-link to="/" class="logo">VentureKeep</router-link>
    <nav>
      <router-link to="/" :class="{ active: route.path === '/' }">Dashboard</router-link>
      <router-link to="/adventurers" :class="{ active: route.path === '/adventurers' }">Adventurers</router-link>
      <router-link to="/parties" :class="{ active: route.path === '/parties' }">Parties</router-link>
      <router-link to="/expeditions" :class="{ active: route.path === '/expeditions' }">Expeditions</router-link>
      <router-link to="/players" :class="{ active: route.path === '/players' }">Players</router-link>
    </nav>
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
</style>
