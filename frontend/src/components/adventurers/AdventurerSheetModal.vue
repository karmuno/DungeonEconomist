<script setup lang="ts">
import { ref, watch } from 'vue'
import * as adventurersApi from '../../api/adventurers'
import type { AdventurerOut } from '../../types'
import { useNotificationsStore } from '../../stores/notifications'
import ModalDialog from '../shared/ModalDialog.vue'
import AdventurerDetail from './AdventurerDetail.vue'

const props = defineProps<{
  adventurerId: number | null
}>()

const emit = defineEmits<{
  close: []
}>()

const notifications = useNotificationsStore()
const adventurer = ref<AdventurerOut | null>(null)

watch(() => props.adventurerId, async (id) => {
  adventurer.value = null
  if (id == null) return
  try {
    adventurer.value = await adventurersApi.getById(id)
  } catch {
    notifications.add('Failed to load adventurer', 'error')
    emit('close')
  }
}, { immediate: true })

async function levelUp() {
  if (!adventurer.value) return
  try {
    const result = await adventurersApi.levelUp(adventurer.value.id)
    notifications.add(`${adventurer.value.name} leveled up to ${result.new_level}! (+${result.hp_gained} HP)`, 'success')
    adventurer.value = await adventurersApi.getById(adventurer.value.id)
  } catch (e) {
    notifications.add((e as { data?: { detail?: string } })?.data?.detail ?? 'Failed to level up', 'error')
  }
}
</script>

<template>
  <ModalDialog
    :is-open="adventurerId != null"
    title="Character Sheet"
    width="420px"
    :z-index="2000"
    @close="emit('close')"
  >
    <AdventurerDetail
      v-if="adventurer"
      :adventurer="adventurer"
      @close="emit('close')"
      @level-up="levelUp"
    />
    <div v-else class="sheet-loading">Loading...</div>
  </ModalDialog>
</template>

<style scoped>
.sheet-loading {
  text-align: center;
  color: #6b7280;
  font-size: 12px;
  padding: 16px 0;
}
</style>
