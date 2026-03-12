<script setup lang="ts">
import { ref } from 'vue'
import type { PartyOut } from '../../types'
import * as partiesApi from '../../api/parties'

const props = defineProps<{
  party: PartyOut
}>()

const emit = defineEmits<{
  updated: []
  cancel: []
}>()

const amount = ref(0)
const action = ref<'add' | 'remove'>('add')

async function onSubmit() {
  const adjustedAmount = action.value === 'remove' ? -amount.value : amount.value
  await partiesApi.updateFunds(props.party.id, { amount: adjustedAmount })
  emit('updated')
}
</script>

<template>
  <form @submit.prevent="onSubmit">
    <p class="mb-2">Current Funds: <span class="text-gold">{{ party.funds }} GP</span></p>

    <div class="form-group mb-2">
      <label class="form-label">Action</label>
      <div class="flex gap-1">
        <label>
          <input v-model="action" type="radio" value="add" /> Add
        </label>
        <label>
          <input v-model="action" type="radio" value="remove" /> Remove
        </label>
      </div>
    </div>

    <div class="form-group mb-2">
      <label class="form-label">Amount (GP)</label>
      <input v-model.number="amount" class="form-input" type="number" min="0" required />
    </div>

    <div class="flex gap-1 mt-3">
      <button type="submit" class="btn btn-primary" :disabled="amount <= 0">Submit</button>
      <button type="button" class="btn btn-secondary" @click="emit('cancel')">Cancel</button>
    </div>
  </form>
</template>
