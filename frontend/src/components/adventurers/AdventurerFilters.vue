<script setup lang="ts">
import { AdventurerClass } from '../../types'

const props = defineProps<{
  modelValue: {
    classFilter: string
    statusFilter: string
    nameSearch: string
    sortBy: string
    sortDir: 'asc' | 'desc'
  }
}>()

const emit = defineEmits<{
  'update:modelValue': [value: typeof props.modelValue]
}>()

function update(field: string, value: string) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

function toggleSortDir() {
  const newDir = props.modelValue.sortDir === 'asc' ? 'desc' : 'asc'
  emit('update:modelValue', { ...props.modelValue, sortDir: newDir })
}

const classOptions = Object.values(AdventurerClass)
</script>

<template>
  <div class="filters-bar">
    <div class="form-group">
      <label class="form-label">Search</label>
      <input
        class="form-input"
        type="text"
        placeholder="Search by name..."
        :value="modelValue.nameSearch"
        @input="update('nameSearch', ($event.target as HTMLInputElement).value)"
      />
    </div>
    <div class="form-group">
      <label class="form-label">Class</label>
      <select
        class="form-select"
        :value="modelValue.classFilter"
        @change="update('classFilter', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">All</option>
        <option v-for="cls in classOptions" :key="cls" :value="cls">{{ cls }}</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Status</label>
      <select
        class="form-select"
        :value="modelValue.statusFilter"
        @change="update('statusFilter', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">All</option>
        <option value="available">Available</option>
        <option value="on_expedition">On Expedition</option>
        <option value="injured">Recovering</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Sort By</label>
      <select
        class="form-select"
        :value="modelValue.sortBy"
        @change="update('sortBy', ($event.target as HTMLSelectElement).value)"
      >
        <option value="name">Name</option>
        <option value="level">Level</option>
        <option value="adventurer_class">Class</option>
        <option value="hp_current">HP</option>
        <option value="xp">XP</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">&nbsp;</label>
      <button class="btn btn-sm" @click="toggleSortDir">
        {{ modelValue.sortDir === 'asc' ? 'ASC' : 'DESC' }}
      </button>
    </div>
  </div>
</template>
