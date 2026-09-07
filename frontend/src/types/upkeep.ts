// Structured upkeep payloads from the backend: the upkeep-day ledger carried
// on the day's GameEvent, and the forecast block on /dashboard/stats.

export interface UpkeepLedgerRow {
  id: number
  name: string
  adventurer_class: string
  level: number
  xp: number
  upkeep_cp: number
  purse_cp: number
  after_cp: number
  outcome: 'paid' | 'sacrificed' | 'prison'
}

export interface UpkeepDayData {
  day: number
  adventurer_count: number
  treasury_before_cp: number
  treasury_after_cp: number
  collected_cp: number
  collected_from: number
  unpaid_cp: number
  prison_names: string[]
  rows: UpkeepLedgerRow[]
}

export interface UpkeepForecastRow {
  id: number
  name: string
  adventurer_class: string
  level: number
  xp: number
  upkeep_cp: number
  purse_cp: number
  short_cp: number
}

export interface UpkeepForecast {
  next_day: number
  days_until: number
  total_cp: number
  treasury_now_cp: number
  rows: UpkeepForecastRow[]
}
