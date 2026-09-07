import type { AdventurerOut, AdventurerRef } from '../types'

export function itemEmoji(itemType: string): string {
  if (itemType === 'weapon') return '\u2694\uFE0F'   // ⚔️
  if (itemType === 'scroll') return '\uD83D\uDCDC'   // 📜
  if (itemType === 'ring')   return '\uD83D\uDC8D'   // 💍
  if (itemType === 'potion') return '\u2697\uFE0F'   // ⚗️
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

export interface TextSegment {
  text: string
  /** Present when this segment is an adventurer's name — click opens their sheet. */
  advId?: number
}

/**
 * Split a notification or popup message into plain and clickable segments, so
 * every adventurer named in it links to their sheet. Only names the backend
 * attached to the event are matched, so a party named after an adventurer is
 * never mistaken for the adventurer.
 *
 * Longest names first: "Rurik the Bold" wins over "Rurik" when both are refs.
 */
export function linkAdventurerNames(text: string, refs: AdventurerRef[]): TextSegment[] {
  if (refs.length === 0) return [{ text }]

  const byLength = [...refs].sort((a, b) => b.name.length - a.name.length)
  const segments: TextSegment[] = []
  let rest = text

  while (rest.length > 0) {
    let bestIndex = -1
    let bestRef: AdventurerRef | null = null
    for (const ref of byLength) {
      if (!ref.name) continue
      const i = rest.indexOf(ref.name)
      if (i !== -1 && (bestIndex === -1 || i < bestIndex)) {
        bestIndex = i
        bestRef = ref
      }
    }
    if (bestIndex === -1 || !bestRef) {
      segments.push({ text: rest })
      break
    }
    if (bestIndex > 0) segments.push({ text: rest.slice(0, bestIndex) })
    segments.push({ text: bestRef.name, advId: bestRef.id })
    rest = rest.slice(bestIndex + bestRef.name.length)
  }

  return segments
}
