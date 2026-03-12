import { computed, reactive, type Ref } from 'vue'
import type { AdventurerOut } from '../types'
import { AdventurerClass } from '../types'

export interface FilterState {
  classFilter: AdventurerClass | ''
  statusFilter: 'available' | 'on_expedition' | 'healing' | ''
  nameSearch: string
  sortBy: 'name' | 'level' | 'hp_current' | 'gold'
  sortDir: 'asc' | 'desc'
}

export function useFilters(adventurers: Ref<AdventurerOut[]>) {
  const filters = reactive<FilterState>({
    classFilter: '',
    statusFilter: '',
    nameSearch: '',
    sortBy: 'name',
    sortDir: 'asc',
  })

  const filtered = computed(() => {
    let result = [...adventurers.value]

    if (filters.classFilter) {
      result = result.filter((a) => a.adventurer_class === filters.classFilter)
    }

    if (filters.statusFilter) {
      switch (filters.statusFilter) {
        case 'available':
          result = result.filter((a) => a.is_available && !a.on_expedition)
          break
        case 'on_expedition':
          result = result.filter((a) => a.on_expedition)
          break
        case 'healing':
          result = result.filter((a) => a.healing_until_day != null)
          break
      }
    }

    if (filters.nameSearch) {
      const search = filters.nameSearch.toLowerCase()
      result = result.filter((a) => a.name.toLowerCase().includes(search))
    }

    return result
  })

  const sorted = computed(() => {
    const list = [...filtered.value]
    const dir = filters.sortDir === 'asc' ? 1 : -1

    list.sort((a, b) => {
      const aVal = a[filters.sortBy]
      const bVal = b[filters.sortBy]

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return dir * aVal.localeCompare(bVal)
      }

      return dir * (Number(aVal) - Number(bVal))
    })

    return list
  })

  return {
    filters,
    filtered,
    sorted,
  }
}
