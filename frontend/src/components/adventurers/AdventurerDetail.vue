<script setup lang="ts">
import { computed } from 'vue'
import type { AdventurerOut } from '../../types'
import ProgressBar from '../shared/ProgressBar.vue'
import InfoTooltip from '../shared/InfoTooltip.vue'
import { formatCurrency } from '../../utils/currency'
import { displayStatus, itemEmoji, itemBonusLabel } from '../../utils/adventurer'

const props = defineProps<{
  adventurer: AdventurerOut
}>()

const emit = defineEmits<{
  close: []
  levelUp: []
}>()

const canLevelUp = computed(() => {
  const adv = props.adventurer
  if (adv.xp_progress != null && adv.xp_progress >= 100) return true
  if (adv.next_level_xp != null && adv.xp >= adv.next_level_xp) return true
  return false
})

const classColor = computed(() => {
  const colors: Record<string, string> = {
    'Fighter': '#e74c3c',
    'Cleric': '#f1c40f',
    'Magic-User': '#9b59b6',
    'Elf': '#2ecc71',
    'Dwarf': '#e67e22',
    'Halfling': '#3498db',
  }
  return colors[props.adventurer.adventurer_class] ?? '#95a5a6'
})

const status = computed(() => displayStatus(props.adventurer))

const hpPct = computed(() => {
  if (props.adventurer.hp_max <= 0) return 0
  return props.adventurer.hp_current / props.adventurer.hp_max
})

const hpBarColor = computed(() => {
  if (props.adventurer.is_dead) return 'var(--accent-red, #e74c3c)'
  if (hpPct.value > 0.5) return 'var(--accent-green, #4ade80)'
  if (hpPct.value > 0.25) return '#fbbf24'
  return 'var(--accent-red, #e74c3c)'
})
</script>

<template>
  <div class="char-sheet">
    <!-- Header -->
    <div class="cs-header" :style="{ borderColor: classColor }">
      <div class="cs-header-top">
        <div class="cs-identity">
          <h2 class="cs-name">{{ adventurer.name }}</h2>
          <span class="cs-class" :style="{ color: classColor }">{{ adventurer.adventurer_class }}</span>
        </div>
        <div class="cs-level-badge" :style="{ backgroundColor: classColor }">
          <span class="cs-level-label">LV</span>
          <span class="cs-level-num">{{ adventurer.level }}</span>
        </div>
      </div>
      <div class="cs-status-row">
        <span class="cs-status" :class="status.toLowerCase().replace(/\s+/g, '-')">{{ status }}</span>
        <span v-if="adventurer.party_name" class="cs-party">{{ adventurer.party_name }}</span>
        <span class="cs-id">#{{ adventurer.id }}</span>
      </div>
    </div>

    <!-- Combat Stats -->
    <div class="cs-combat-row">
      <div class="cs-stat">
        <span class="cs-stat-value">{{ adventurer.thac0 ?? '—' }}</span>
        <span class="cs-stat-label">THAC0 <InfoTooltip text="To Hit Armor Class 0. The d20 roll needed to hit AC 0. Lower is better." /></span>
      </div>
      <div class="cs-stat">
        <span class="cs-stat-value">{{ adventurer.hit_dice ?? '—' }}</span>
        <span class="cs-stat-label">HD <InfoTooltip text="Hit Dice. Determines HP gained on level up and combat effectiveness." /></span>
      </div>
      <div class="cs-stat">
        <span class="cs-stat-value">{{ adventurer.to_hit_bonus ? '+' + adventurer.to_hit_bonus : '+0' }}</span>
        <span class="cs-stat-label">ATK <InfoTooltip text="Attack bonus from class and magic weapons." /></span>
      </div>
      <div class="cs-stat">
        <span class="cs-stat-value cs-gold-value">{{ formatCurrency(adventurer.gold, adventurer.silver, adventurer.copper) }}</span>
        <span class="cs-stat-label">WEALTH</span>
      </div>
    </div>

    <!-- HP & XP -->
    <div class="cs-bars">
      <div class="cs-bar-group">
        <span class="cs-bar-label">HP</span>
        <ProgressBar :value="adventurer.hp_current" :max="adventurer.hp_max" :color="hpBarColor" />
      </div>
      <div class="cs-bar-group">
        <span class="cs-bar-label">XP</span>
        <template v-if="adventurer.next_level_xp != null">
          <ProgressBar
            :value="adventurer.xp - (adventurer.current_level_xp ?? 0)"
            :max="adventurer.next_level_xp - (adventurer.current_level_xp ?? 0)"
            color="var(--accent-blue)"
          />
        </template>
        <div v-else class="cs-xp-max">
          <span>{{ adventurer.xp }} XP</span>
          <span class="cs-max-badge">MAX</span>
        </div>
      </div>
    </div>

    <!-- Class Ability -->
    <div v-if="adventurer.class_ability" class="cs-ability">
      <span class="cs-ability-icon" :style="{ color: classColor }">&#9670;</span>
      <span class="cs-ability-text">{{ adventurer.class_ability }}</span>
    </div>

    <!-- Equipment -->
    <div class="cs-section">
      <span class="cs-section-title">Equipment</span>
      <div v-if="adventurer.magic_items && adventurer.magic_items.length > 0" class="cs-items">
        <div v-for="item in adventurer.magic_items" :key="item.id" class="cs-item">
          <span class="cs-item-icon">{{ itemEmoji(item.item_type) }}</span>
          <span class="cs-item-name">{{ item.name }}</span>
          <span v-if="itemBonusLabel(item.item_type, item.bonus)" class="cs-item-bonus">
            {{ itemBonusLabel(item.item_type, item.bonus) }}
          </span>
        </div>
      </div>
      <div v-else class="cs-no-items">No equipment</div>
    </div>

    <!-- Death / Bankruptcy -->
    <div v-if="adventurer.is_dead" class="cs-death">
      Fell on day {{ adventurer.death_day }}<template v-if="adventurer.death_party_name"> with {{ adventurer.death_party_name }}</template>
    </div>
    <div v-if="adventurer.is_bankrupt" class="cs-death">
      Sent to debtor's prison on day {{ adventurer.bankruptcy_day }}
    </div>

    <!-- Actions -->
    <div class="cs-actions">
      <button
        v-if="canLevelUp"
        class="btn btn-primary"
        @click="emit('levelUp')"
      >
        Level Up
      </button>
      <button class="btn btn-secondary" @click="emit('close')">Close</button>
    </div>
  </div>
</template>

<style scoped>
.char-sheet {
  padding: 0;
}

/* Header */
.cs-header {
  border-left: 4px solid;
  padding: 8px 12px;
  margin-bottom: 12px;
  background: var(--bg-secondary);
  border-radius: 0 var(--border-radius) var(--border-radius) 0;
}

.cs-header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.cs-identity {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.cs-name {
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0;
  line-height: 1.2;
}

.cs-class {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.cs-level-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--border-radius);
  color: #000;
  font-weight: 700;
  line-height: 1;
}

.cs-level-label {
  font-size: 8px;
  letter-spacing: 1px;
}

.cs-level-num {
  font-size: 1.4rem;
}

.cs-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 11px;
}

.cs-status {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
}

.cs-status.available { background: rgba(74, 222, 128, 0.15); color: #4ade80; }
.cs-status.on-expedition { background: rgba(96, 165, 250, 0.15); color: #60a5fa; }
.cs-status.recovering { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.cs-status.assigned { background: rgba(168, 85, 247, 0.15); color: #a855f7; }
.cs-status.dead { background: rgba(231, 76, 60, 0.2); color: #e74c3c; }
.cs-status.bankrupt { background: rgba(231, 76, 60, 0.15); color: #e74c3c; }
.cs-status.unavailable { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }

.cs-party {
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.cs-id {
  color: var(--text-muted);
  font-family: var(--font-mono);
  margin-left: auto;
}

/* Combat Stats */
.cs-combat-row {
  display: flex;
  gap: 2px;
  margin-bottom: 12px;
}

.cs-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 4px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.cs-stat-value {
  font-size: 1rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-primary);
}

.cs-gold-value {
  font-size: 0.75rem;
  color: var(--accent-green);
}

.cs-stat-label {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  font-weight: 600;
}

/* HP & XP Bars */
.cs-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.cs-bar-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cs-bar-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
  width: 20px;
  text-align: right;
}

.cs-bar-group :deep(.progress-bar) {
  flex: 1;
}

.cs-xp-row {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.cs-xp-row :deep(.progress-bar) {
  flex: 1;
}

.cs-xp-numbers {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  text-align: right;
}

.cs-xp-max {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.cs-max-badge {
  font-size: 9px;
  font-weight: 700;
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.15);
  padding: 1px 5px;
  border-radius: 3px;
}

/* Class Ability */
.cs-ability {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin-bottom: 12px;
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.cs-ability-icon {
  font-size: 10px;
  flex-shrink: 0;
  margin-top: 2px;
}

/* Equipment */
.cs-section {
  margin-bottom: 12px;
}

.cs-section-title {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  font-weight: 600;
  display: block;
  margin-bottom: 4px;
}

.cs-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cs-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  font-size: 12px;
}

.cs-item-icon {
  font-size: 13px;
  flex-shrink: 0;
}

.cs-item-name {
  flex: 1;
  color: #fbbf24;
  font-weight: 600;
}

.cs-item-bonus {
  font-family: var(--font-mono);
  color: var(--accent-green);
  font-size: 11px;
  font-weight: 600;
}

.cs-no-items {
  font-size: 11px;
  color: var(--text-muted);
  padding: 4px 6px;
}

/* Death */
.cs-death {
  font-size: 11px;
  color: var(--accent-red, #e74c3c);
  padding: 4px 6px;
  background: rgba(231, 76, 60, 0.1);
  border-radius: 3px;
  margin-bottom: 8px;
}

/* Actions */
.cs-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
