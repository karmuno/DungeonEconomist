<script setup lang="ts">
import { ref } from 'vue'
import { AdventurerClass } from '../../types'

export interface FilterState {
  classFilter: string
  statuses: Set<string>
  nameSearch: string
  sortBy: string
  sortDir: 'asc' | 'desc'
}

const ALL_STATUSES = ['Available', 'Recovering', 'On Expedition', 'Dead', 'Bankrupt'] as const

const props = defineProps<{
  modelValue: FilterState
}>()

const emit = defineEmits<{
  'update:modelValue': [value: FilterState]
}>()

const showStatusModal = ref(false)

function update(field: string, value: unknown) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

function toggleStatus(status: string) {
  const next = new Set(props.modelValue.statuses)
  if (next.has(status)) {
    next.delete(status)
  } else {
    next.add(status)
  }
  emit('update:modelValue', { ...props.modelValue, statuses: next })
}

function toggleSortDir() {
  const newDir = props.modelValue.sortDir === 'asc' ? 'desc' : 'asc'
  emit('update:modelValue', { ...props.modelValue, sortDir: newDir })
}

const classOptions = Object.values(AdventurerClass)

const activeCount = (() => {
  return props.modelValue.statuses.size
})
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
      <button class="btn btn-sm status-filter-btn" @click="showStatusModal = !showStatusModal">
        {{ modelValue.statuses.size }} of {{ ALL_STATUSES.length }}
      </button>
      <div v-if="showStatusModal" class="status-dropdown">
        <label
          v-for="status in ALL_STATUSES"
          :key="status"
          class="status-option"
          :class="{ active: modelValue.statuses.has(status) }"
          @click.prevent="toggleStatus(status)"
        >
          <span class="status-check">{{ modelValue.statuses.has(status) ? '✓' : '' }}</span>
          <span>{{ status }}</span>
        </label>
      </div>
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

<style scoped>
.status-filter-btn {
  min-width: 80px;
}

.status-dropdown {
  position: absolute;
  z-index: 50;
  margin-top: 4px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 4px 0;
  min-width: 160px;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  transition: background 0.1s;
}

.status-option:hover {
  background: var(--bg-secondary);
}

.status-option.active {
  color: var(--text-primary);
}

.status-check {
  width: 16px;
  text-align: center;
  color: var(--accent-green);
  font-weight: 700;
}

.form-group {
  position: relative;
}
</style>
