<script setup lang="ts">
import { ref } from 'vue'
import type { PartyOut } from '../../types'
import * as partiesApi from '../../api/parties'

const props = defineProps<{
  party?: PartyOut
}>()

const emit = defineEmits<{
  saved: [party?: PartyOut]
  cancel: []
}>()

const form = ref({
  name: props.party?.name ?? '',
})

const submitting = ref(false)
const error = ref('')

async function onSubmit() {
  submitting.value = true
  error.value = ''
  try {
    const data = {
      name: form.value.name,
    }
    let result: PartyOut
    if (props.party) {
      result = await partiesApi.update(props.party.id, data)
    } else {
      result = await partiesApi.create(data)
    }
    emit('saved', result)
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

    <div class="flex gap-1 mt-3">
      <button type="submit" class="btn btn-primary" :disabled="submitting">
        {{ party ? 'Update' : 'Create' }}
      </button>
      <button type="button" class="btn btn-secondary" @click="emit('cancel')">Cancel</button>
    </div>
  </form>
</template>
