<script setup lang="ts">
import { computed } from 'vue'
import type { AdventurerRef } from '../../types'
import { linkAdventurerNames } from '../../utils/adventurer'

// Any prose that names adventurers: each name the roster knows becomes a link
// to their sheet. Only names in `refs` are matched, so a party named after an
// adventurer is never mistaken for one.
const props = defineProps<{
  text: string
  refs: AdventurerRef[]
}>()

const emit = defineEmits<{
  open: [id: number]
}>()

const segments = computed(() => linkAdventurerNames(props.text, props.refs))
</script>

<template>
  <span><template v-for="(seg, i) in segments" :key="i"><span
    v-if="seg.advId"
    class="adv-link"
    @click.stop="emit('open', seg.advId)"
  >{{ seg.text }}</span><template v-else>{{ seg.text }}</template></template></span>
</template>

<style scoped>
.adv-link {
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: #374151;
  text-underline-offset: 2px;
}

.adv-link:hover {
  color: #4ade80;
  text-decoration-color: #4ade80;
}
</style>
