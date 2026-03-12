<script setup lang="ts">
import { ref } from 'vue'
import * as playersApi from '../../api/players'

const emit = defineEmits<{
  created: []
  cancel: []
}>()

const name = ref('')
const submitting = ref(false)
const error = ref('')

async function onSubmit() {
  submitting.value = true
  error.value = ''
  try {
    await playersApi.create({ name: name.value })
    emit('created')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to create player'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form @submit.prevent="onSubmit">
    <div v-if="error" class="text-danger mb-2">{{ error }}</div>

    <div class="form-group mb-2">
      <label class="form-label">Player Name</label>
      <input v-model="name" class="form-input" type="text" required />
    </div>

    <div class="flex gap-1 mt-3">
      <button type="submit" class="btn btn-primary" :disabled="submitting">Create</button>
      <button type="button" class="btn btn-secondary" @click="emit('cancel')">Cancel</button>
    </div>
  </form>
</template>
