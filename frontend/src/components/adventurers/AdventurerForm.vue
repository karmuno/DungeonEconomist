<script setup lang="ts">
import { ref, reactive } from 'vue'
import { AdventurerClass } from '../../types'
import type { AdventurerCreate } from '../../types'
import * as adventurersApi from '../../api/adventurers'
import { useNotificationsStore } from '../../stores/notifications'

const emit = defineEmits<{
  created: []
  cancel: []
}>()

const notifications = useNotificationsStore()

const form = reactive<AdventurerCreate>({
  name: '',
  adventurer_class: AdventurerClass.FIGHTER,
  hp_max: 8,
})

const submitting = ref(false)
const error = ref('')

const classOptions = Object.values(AdventurerClass)

async function onSubmit() {
  error.value = ''
  if (!form.name.trim()) {
    error.value = 'Name is required'
    return
  }

  submitting.value = true
  try {
    await adventurersApi.create(form)
    notifications.add(`Adventurer "${form.name}" created!`, 'success')
    emit('created')
  } catch (err: any) {
    error.value = err?.response?.data?.detail || err?.message || 'Failed to create adventurer'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form @submit.prevent="onSubmit">
    <div v-if="error" class="mb-2" style="color: var(--accent-red)">
      {{ error }}
    </div>

    <div class="form-group mb-2">
      <label class="form-label">Name</label>
      <input v-model="form.name" class="form-input" type="text" placeholder="Adventurer name" />
    </div>

    <div class="form-group mb-2">
      <label class="form-label">Class</label>
      <select v-model="form.adventurer_class" class="form-select">
        <option v-for="cls in classOptions" :key="cls" :value="cls">{{ cls }}</option>
      </select>
    </div>

    <div class="form-group mb-3">
      <label class="form-label">Max HP</label>
      <input v-model.number="form.hp_max" class="form-input" type="number" min="1" />
    </div>

    <div class="flex gap-1">
      <button class="btn btn-primary" type="submit" :disabled="submitting">
        {{ submitting ? 'Creating...' : 'Create Adventurer' }}
      </button>
      <button class="btn" type="button" @click="emit('cancel')">Cancel</button>
    </div>
  </form>
</template>
