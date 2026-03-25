import type { AdventurerOut } from '../types'

export function itemEmoji(itemType: string): string {
  if (itemType === 'weapon') return '\u2694\uFE0F'   // ⚔️
  if (itemType === 'scroll') return '\uD83D\uDCDC'   // 📜
  return '\uD83D\uDEE1\uFE0F'                        // 🛡️
}

/** Returns the bonus label (e.g. "+2") or empty string for consumables with no meaningful bonus. */
export function itemBonusLabel(itemType: string, bonus: number): string {
  if (itemType === 'scroll' || itemType === 'potion') return ''
  return `+${bonus}`
}

export function displayStatus(adv: AdventurerOut): string {
  if (adv.is_dead) return 'Dead'
  if (adv.is_bankrupt) return 'Bankrupt'
  if (adv.on_expedition) return 'On Expedition'
  if (adv.is_assigned) return 'Assigned'
  if (adv.hp_current < adv.hp_max) return 'Recovering'
  if (adv.is_available) return 'Available'
  return 'Unavailable'
}
