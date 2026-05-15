import type { DayReport, DayReportEntry, DayReportEntryType, DayReportSection, GameEvent } from '../types'
import { formatGameDay } from './calendar'

/**
 * Map a backend GameEvent.type to a DayReport entry color/dot category.
 * The modal drives its dot color off this value.
 */
const TYPE_MAP: Record<string, DayReportEntryType> = {
  recruitment: 'tavern',
  tavern: 'tavern',
  healing: 'healing',
  expedition_complete: 'info',
  auto_start: 'info',
  upkeep: 'upkeep',
  expedition_choice: 'choice',
  stairs: 'choice',
  stairs_discovered: 'choice',
  level_up: 'info',
  death: 'combat',
  combat: 'combat',
  loot: 'loot',
}

function classifyEvent(type: string): DayReportEntryType {
  return TYPE_MAP[type] ?? 'info'
}

function buildEntry(event: GameEvent): DayReportEntry {
  const t = classifyEvent(event.type)
  const entry: DayReportEntry = { t, text: event.message }
  if (t === 'choice') entry.choice = true
  return entry
}

/**
 * Build a DayReport payload from a batch of GameEvents returned by advance-day
 * or skip-to-event. Events are grouped by expedition_id (each becomes an
 * "Expedition #{id}" section) with remaining events collected under "Keep".
 *
 * v1 is a pure client-side aggregator; the backend can later return structured
 * DayReport payloads directly without changing this component's contract.
 */
interface ExpeditionGroup {
  title: string
  entries: DayReportEntry[]
}

export function buildDayReport(
  day: number,
  events: GameEvent[],
  treasuryBefore: { g: number; s: number; c: number },
  treasuryAfter: { g: number; s: number; c: number },
): DayReport {
  const expeditionGroups = new Map<number, ExpeditionGroup>()
  const keepEntries: DayReportEntry[] = []

  for (const event of events) {
    const entry = buildEntry(event)
    if (event.expedition_id) {
      const group = expeditionGroups.get(event.expedition_id)
      if (group) {
        group.entries.push(entry)
        // Upgrade to a named title if an event in this group supplies a party_name.
        if (event.party_name && group.title === `Expedition #${event.expedition_id}`) {
          group.title = event.party_name
        }
      } else {
        const title = event.party_name || `Expedition #${event.expedition_id}`
        expeditionGroups.set(event.expedition_id, { title, entries: [entry] })
      }
    } else {
      keepEntries.push(entry)
    }
  }

  const sections: DayReportSection[] = []
  for (const group of expeditionGroups.values()) {
    sections.push({
      title: group.title,
      kind: 'expedition',
      entries: group.entries,
    })
  }
  if (keepEntries.length > 0) {
    sections.push({
      title: 'Keep',
      kind: 'keep',
      entries: keepEntries,
    })
  }

  return {
    day,
    calendar: formatGameDay(day),
    treasuryBefore,
    treasuryAfter,
    sections,
  }
}
