import type { AdventurerOut } from '../types'

export function displayStatus(adv: AdventurerOut): string {
  if (adv.is_dead) return 'Dead'
  if (adv.is_bankrupt) return 'Bankrupt'
  if (adv.on_expedition) return 'On Expedition'
  if (adv.hp_current < adv.hp_max) return 'Recovering'
  if (adv.is_available) return 'Available'
  return 'Unavailable'
}
