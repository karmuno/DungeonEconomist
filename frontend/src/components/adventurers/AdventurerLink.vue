<script setup lang="ts">
import { useAdventurerSheet } from '../../composables/useAdventurerSheet'

const { advName, dead } = defineProps<{
  advName: string
  dead?: boolean
}>()

const { openByName } = useAdventurerSheet()
</script>

<template>
  <span
    class="adv-link"
    :class="{ dead }"
    @click.stop="openByName(advName)"
  >{{ advName }}</span>
</template>

<style scoped>
.adv-link {
  display: inline;
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: transparent;
  transition: text-decoration-color 0.15s;
}

.adv-link:hover {
  text-decoration-color: currentColor;
}

.adv-link.dead {
  text-decoration: line-through;
  opacity: 0.6;
}
</style>
