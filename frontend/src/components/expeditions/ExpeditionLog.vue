<script setup lang="ts">
defineProps<{
  log: unknown[]
}>()

function getTurnSummary(turn: unknown): string {
  if (typeof turn === 'object' && turn !== null) {
    const t = turn as Record<string, unknown>
    const parts: string[] = []
    if (t.event_type) parts.push(String(t.event_type))
    if (t.combat_outcome) parts.push(`Combat: ${t.combat_outcome}`)
    if (t.treasure_found) parts.push(`Treasure: ${t.treasure_found} GP`)
    if (t.description) parts.push(String(t.description))
    return parts.join(' | ') || JSON.stringify(turn)
  }
  return String(turn)
}

function getTurnNumber(turn: unknown, index: number): number {
  if (typeof turn === 'object' && turn !== null) {
    const t = turn as Record<string, unknown>
    if (typeof t.turn === 'number') return t.turn
    if (typeof t.turn_number === 'number') return t.turn_number
  }
  return index + 1
}
</script>

<template>
  <div>
    <h4 class="mb-2">Expedition Log</h4>
    <div v-if="log.length === 0" class="text-muted">No log entries</div>
    <details v-for="(turn, index) in log" :key="index" class="mb-1">
      <summary>Turn {{ getTurnNumber(turn, index) }}: {{ getTurnSummary(turn) }}</summary>
      <pre class="mt-1 text-muted" style="white-space: pre-wrap; font-size: 0.85em;">{{ JSON.stringify(turn, null, 2) }}</pre>
    </details>
  </div>
</template>
