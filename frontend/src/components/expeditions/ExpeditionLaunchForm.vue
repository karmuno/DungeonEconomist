<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { PartyOut } from '../../types'
import * as partiesApi from '../../api/parties'
import * as expeditionsApi from '../../api/expeditions'

const props = defineProps<{
  preselectedPartyId?: number
}>()

const emit = defineEmits<{
  launched: []
  cancel: []
}>()

const parties = ref<PartyOut[]>([])
const selectedPartyId = ref<number | null>(props.preselectedPartyId ?? null)
const dungeonLevel = ref(1)
const submitting = ref(false)

const availableParties = computed(() =>
  parties.value.filter((p) => !p.on_expedition && p.members.length > 0)
)

onMounted(async () => {
  parties.value = await partiesApi.list()
  if (props.preselectedPartyId && availableParties.value.some((p) => p.id === props.preselectedPartyId)) {
    selectedPartyId.value = props.preselectedPartyId
  }
})

async function onSubmit() {
  if (!selectedPartyId.value) return
  submitting.value = true
  try {
    await expeditionsApi.launch({
      party_id: selectedPartyId.value,
      dungeon_level: dungeonLevel.value,
      duration_days: 7,
    })
    emit('launched')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form @submit.prevent="onSubmit">
    <div class="form-group mb-2">
      <label class="form-label">Party</label>
      <select v-model="selectedPartyId" class="form-select" required>
        <option :value="null" disabled>Select a party</option>
        <option v-for="party in availableParties" :key="party.id" :value="party.id">
          {{ party.name }} ({{ party.members.length }} members)
        </option>
      </select>
    </div>

    <div class="form-group mb-2">
      <label class="form-label">Dungeon Level: {{ dungeonLevel }}</label>
      <input v-model.number="dungeonLevel" type="range" min="1" max="6" class="form-input" />
    </div>

    <div class="form-group mb-2">
      <label class="form-label">Duration</label>
      <p class="text-muted">7 days (fixed)</p>
    </div>

    <div class="flex gap-1 mt-3">
      <button type="submit" class="btn btn-primary" :disabled="submitting || !selectedPartyId">Launch</button>
      <button type="button" class="btn btn-secondary" @click="emit('cancel')">Cancel</button>
    </div>
  </form>
</template>
