<script setup lang="ts">
import cup from '../../assets/bmc-cup.png'

const BMC_URL = 'https://buymeacoffee.com/codyjanegames'
</script>

<template>
  <a class="bmc-chip" :href="BMC_URL" target="_blank" rel="noopener">
    <img :src="cup" alt="" class="bmc-cup" />
    <span>Buy me a coffee</span>
  </a>
</template>

<style scoped>
/* design_handoff_bmc_chip/bmc-chip-gold.html */
.bmc-chip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 36px;
  border-radius: var(--border-radius);
  background: var(--accent-gold);
  color: #0d0c22;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
  transition: opacity 0.15s;
}

.bmc-chip:hover {
  color: #0d0c22;
  opacity: 0.85;
}

.bmc-cup {
  display: block;
  height: 20px;
  width: auto;
}
</style>
