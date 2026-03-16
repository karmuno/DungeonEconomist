<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { AdventurerClass } from '../../types'

export interface FilterState {
  classFilter: string
  statuses: Set<string>
  nameSearch: string
  sortBy: string
  sortDir: 'asc' | 'desc'
}

const ALL_STATUSES = ['Available', 'Recovering', 'On Expedition', 'Assigned', 'Dead', 'Bankrupt'] as const

const props = defineProps<{
  modelValue: FilterState
}>()

const emit = defineEmits<{
  'update:modelValue': [value: FilterState]
}>()

const showStatusDropdown = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

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

function statusLabel(): string {
  const s = props.modelValue.statuses
  if (s.size === 0) return 'None'
  if (s.size === ALL_STATUSES.length) return 'All'
  return [...s].join(', ')
}

// Close dropdown on outside click
function onClickOutside(e: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
    showStatusDropdown.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))

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
    <div class="form-group" ref="dropdownRef">
      <label class="form-label">Status</label>
      <button
        class="form-select status-trigger"
        @click.stop="showStatusDropdown = !showStatusDropdown"
      >
        {{ statusLabel() }}
      </button>
      <div v-if="showStatusDropdown" class="status-dropdown">
        <div
          v-for="status in ALL_STATUSES"
          :key="status"
          class="status-option"
          :class="{ active: modelValue.statuses.has(status) }"
          @click.stop="toggleStatus(status)"
        >
          <span class="status-check">{{ modelValue.statuses.has(status) ? '&#10003;' : '' }}</span>
          <span>{{ status }}</span>
        </div>
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
        <option value="party">Party</option>
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
.form-group {
  position: relative;
}

.status-trigger {
  text-align: left;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 150px;
}

.status-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 50;
  margin-top: 2px;
  background: var(--bg-input, var(--bg-primary));
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  min-width: 180px;
  padding: 4px 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.status-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 0.825rem;
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
  font-size: 12px;
}
</style>
