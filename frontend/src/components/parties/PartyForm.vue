<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { PartyOut, PlayerOut } from '../../types'
import * as partiesApi from '../../api/parties'
import * as playersApi from '../../api/players'

const props = defineProps<{
  party?: PartyOut
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const form = ref({
  name: props.party?.name ?? '',
  funds: props.party?.funds ?? 0,
  player_id: props.party?.player_id ?? null as number | null,
})

const players = ref<PlayerOut[]>([])
const submitting = ref(false)
const error = ref('')

onMounted(async () => {
  players.value = await playersApi.list()
})

async function onSubmit() {
  submitting.value = true
  error.value = ''
  try {
    const data = {
      name: form.value.name,
      funds: form.value.funds,
      player_id: form.value.player_id || null,
    }
    if (props.party) {
      await partiesApi.update(props.party.id, data)
    } else {
      await partiesApi.create(data)
    }
    emit('saved')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to save party'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form @submit.prevent="onSubmit">
    <div v-if="error" class="text-danger mb-2">{{ error }}</div>

    <div class="form-group mb-2">
      <label class="form-label">Party Name</label>
      <input v-model="form.name" class="form-input" type="text" required />
    </div>

    <div class="form-group mb-2">
      <label class="form-label">Starting Funds (GP)</label>
      <input v-model.number="form.funds" class="form-input" type="number" min="0" />
    </div>

    <div class="form-group mb-2">
      <label class="form-label">Player</label>
      <select v-model="form.player_id" class="form-select">
        <option :value="null">None</option>
        <option v-for="player in players" :key="player.id" :value="player.id">
          {{ player.name }}
        </option>
      </select>
    </div>

    <div class="flex gap-1 mt-3">
      <button type="submit" class="btn btn-primary" :disabled="submitting">
        {{ party ? 'Update' : 'Create' }}
      </button>
      <button type="button" class="btn btn-secondary" @click="emit('cancel')">Cancel</button>
    </div>
  </form>
</template>
