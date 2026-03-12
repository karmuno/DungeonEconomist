<script setup lang="ts">
import type { PartyOut } from '../../types'
import StatusBadge from '../shared/StatusBadge.vue'

defineProps<{
  party: PartyOut
}>()

const emit = defineEmits<{
  select: []
  manage: []
  launch: []
}>()
</script>

<template>
  <div class="party-card card">
    <div class="card-header flex flex-between">
      <h3>{{ party.name }}</h3>
      <StatusBadge :status="party.on_expedition ? 'On Expedition' : 'Available'" />
    </div>
    <div class="card-body">
      <p>{{ party.members.length }} members</p>
      <p class="text-gold">{{ party.funds }} GP</p>
      <div class="mt-1">
        <span
          v-for="member in party.members.slice(0, 4)"
          :key="member.id"
          class="badge"
        >
          {{ member.name }} ({{ member.adventurer_class }})
        </span>
        <span v-if="party.members.length > 4" class="text-muted">
          +{{ party.members.length - 4 }} more
        </span>
      </div>
    </div>
    <div class="card-footer flex gap-1">
      <button class="btn btn-secondary btn-sm" @click="emit('manage')">Manage</button>
      <button
        class="btn btn-primary btn-sm"
        :disabled="party.on_expedition || party.members.length === 0"
        @click="emit('launch')"
      >
        Launch Expedition
      </button>
    </div>
  </div>
</template>
