<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { PartyOut, SupplyOut } from '../../types'
import { SupplyType } from '../../types'
import * as suppliesApi from '../../api/supplies'
import * as partiesApi from '../../api/parties'

const props = defineProps<{
  party: PartyOut
}>()

const emit = defineEmits<{
  updated: []
}>()

const allSupplies = ref<SupplyOut[]>([])
const typeFilter = ref('')
const loading = ref(false)

const filteredSupplies = computed(() => {
  if (!typeFilter.value) return allSupplies.value
  return allSupplies.value.filter((s) => s.type === typeFilter.value)
})

onMounted(async () => {
  loading.value = true
  allSupplies.value = await suppliesApi.list()
  loading.value = false
})

async function buySupply(supplyId: number) {
  loading.value = true
  await partiesApi.addSupply(props.party.id, {
    party_id: props.party.id,
    supply_id: supplyId,
    quantity: 1,
  })
  emit('updated')
  loading.value = false
}

async function removeSupply(supplyId: number) {
  loading.value = true
  await partiesApi.removeSupply(props.party.id, supplyId, 1)
  emit('updated')
  loading.value = false
}
</script>

<template>
  <div class="flex gap-1">
    <div style="flex: 1">
      <h4 class="mb-2">Party Supplies</h4>
      <div v-if="!party.supplies || party.supplies.length === 0" class="text-muted">No supplies</div>
      <div v-for="ps in party.supplies" :key="ps.supply.id" class="flex flex-between mb-1">
        <span>
          {{ ps.supply.name }}
          <span class="badge">{{ ps.supply.type }}</span>
          <span class="text-muted">x{{ ps.quantity }}</span>
          <span class="text-gold">{{ ps.supply.cost }} GP</span>
        </span>
        <button class="btn btn-danger btn-sm" @click="removeSupply(ps.supply.id)">Remove</button>
      </div>
    </div>

    <div style="flex: 1">
      <h4 class="mb-2">Available Supplies</h4>
      <div class="filters-bar mb-2">
        <select v-model="typeFilter" class="form-select">
          <option value="">All Types</option>
          <option v-for="t in Object.values(SupplyType)" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
      <div v-if="loading" class="text-muted">Loading...</div>
      <div v-else-if="filteredSupplies.length === 0" class="text-muted">No supplies available</div>
      <div v-for="supply in filteredSupplies" :key="supply.id" class="flex flex-between mb-1">
        <span>
          {{ supply.name }}
          <span class="badge">{{ supply.type }}</span>
          <span class="text-gold">{{ supply.cost }} GP</span>
        </span>
        <button class="btn btn-primary btn-sm" @click="buySupply(supply.id)">Add</button>
      </div>
    </div>
  </div>
</template>
