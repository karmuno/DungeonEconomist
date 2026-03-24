<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { PartyOut, AdventurerOut } from '../../types'
import * as adventurersApi from '../../api/adventurers'
import * as partiesApi from '../../api/parties'
import ConfirmButton from '../shared/ConfirmButton.vue'

const props = defineProps<{
  party: PartyOut
}>()

const emit = defineEmits<{
  updated: []
}>()

const allAdventurers = ref<AdventurerOut[]>([])
const classFilter = ref('')
const levelFilter = ref<number | null>(null)
const loading = ref(false)

const memberIds = computed(() => new Set(props.party.members.map((m) => m.id)))

const availableAdventurers = computed(() => {
  return allAdventurers.value.filter((a) => {
    if (memberIds.value.has(a.id)) return false
    if (!a.is_available) return false
    if (classFilter.value && a.adventurer_class !== classFilter.value) return false
    if (levelFilter.value && a.level < levelFilter.value) return false
    return true
  })
})

onMounted(async () => {
  loading.value = true
  allAdventurers.value = await adventurersApi.list()
  loading.value = false
})

async function addMember(adventurerId: number) {
  loading.value = true
  await partiesApi.addMember({ party_id: props.party.id, adventurer_id: adventurerId })
  emit('updated')
  allAdventurers.value = await adventurersApi.list()
  loading.value = false
}

async function removeMember(adventurerId: number) {
  loading.value = true
  await partiesApi.removeMember({ party_id: props.party.id, adventurer_id: adventurerId })
  emit('updated')
  allAdventurers.value = await adventurersApi.list()
  loading.value = false
}
</script>

<template>
  <div class="flex gap-1">
    <div style="flex: 1">
      <h4 class="mb-2">Current Members</h4>
      <div v-if="party.members.length === 0" class="text-muted">No members yet</div>
      <div v-for="member in party.members" :key="member.id" class="flex flex-between mb-1">
        <span>
          {{ member.name }}
          <span class="badge">{{ member.adventurer_class }}</span>
          <span class="text-muted">Lv {{ member.level }}</span>
        </span>
        <ConfirmButton label="Remove" confirm-label="Sure?" variant="danger" @confirm="removeMember(member.id)" />
      </div>
    </div>

    <div style="flex: 1">
      <h4 class="mb-2">Available Adventurers</h4>
      <div class="filters-bar mb-2 flex gap-1">
        <select v-model="classFilter" class="form-select">
          <option value="">All Classes</option>
          <option v-for="cls in ['Fighter', 'Cleric', 'Magic-User', 'Elf', 'Dwarf', 'Halfling']" :key="cls" :value="cls">
            {{ cls }}
          </option>
        </select>
        <input
          v-model.number="levelFilter"
          class="form-input"
          type="number"
          placeholder="Min level"
          min="1"
        />
      </div>
      <div v-if="loading" class="text-muted">Loading...</div>
      <div v-else-if="availableAdventurers.length === 0" class="text-muted">No available adventurers</div>
      <div v-for="adv in availableAdventurers" :key="adv.id" class="flex flex-between mb-1">
        <span>
          {{ adv.name }}
          <span class="badge">{{ adv.adventurer_class }}</span>
          <span class="text-muted">Lv {{ adv.level }}</span>
        </span>
        <button class="btn btn-primary btn-sm" @click="addMember(adv.id)">Add</button>
      </div>
    </div>
  </div>
</template>
