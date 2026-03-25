<script setup lang="ts">
import type { AdventurerOut } from '../../types'
import ProgressBar from '../shared/ProgressBar.vue'
import StatusBadge from '../shared/StatusBadge.vue'
import EmptyState from '../shared/EmptyState.vue'
import { formatCurrency } from '../../utils/currency'
import { displayStatus, itemEmoji, itemBonusLabel } from '../../utils/adventurer'

const props = defineProps<{
  adventurers: AdventurerOut[]
  partyNameMap?: Record<number, string>
  hideHp?: boolean
}>()

const emit = defineEmits<{
  select: [id: number]
}>()

function partyDisplay(adv: AdventurerOut): string {
  if (adv.is_dead && adv.death_party_name) return adv.death_party_name
  return props.partyNameMap?.[adv.id] ?? '—'
}
</script>

<template>
  <table v-if="adventurers.length > 0" class="table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Items</th>
        <th>Class</th>
        <th>Level</th>
        <th>Party</th>
        <th v-if="!hideHp" style="width: 160px">HP</th>
        <th>XP</th>
        <th>Gold</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="adv in adventurers"
        :key="adv.id"
        style="cursor: pointer"
        @click="emit('select', adv.id)"
      >
        <td>{{ adv.name }}</td>
        <td>
          <span v-for="item in (adv.magic_items || [])" :key="item.id" class="item-tag" :title="item.name">{{ itemEmoji(item.item_type) }}{{ itemBonusLabel(item.item_type, item.bonus) }}</span>
        </td>
        <td>{{ adv.adventurer_class }}</td>
        <td>{{ adv.level }}</td>
        <td>{{ partyDisplay(adv) }}</td>
        <td v-if="!hideHp">
          <ProgressBar :value="adv.hp_current" :max="adv.hp_max" />
        </td>
        <td>{{ adv.xp }}</td>
        <td class="text-gold">{{ formatCurrency(adv.gold, adv.silver, adv.copper) }}</td>
        <td><StatusBadge :status="displayStatus(adv)" /></td>
      </tr>
    </tbody>
  </table>
  <EmptyState v-else message="No adventurers found" />
</template>

<style scoped>
.item-tag {
  font-size: 11px;
  font-family: var(--font-mono);
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.1);
  padding: 1px 4px;
  border-radius: 3px;
  white-space: nowrap;
  margin-right: 2px;
}
</style>
