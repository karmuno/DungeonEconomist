/**
 * Format a game day number into a calendar display.
 * 30 days/month, 12 months/year (360 days/year).
 * Returns "Month X, Day Y, Year Z" format.
 */
export function formatGameDay(day: number): string {
  if (day <= 0) return 'Day 0'

  const year = Math.ceil(day / 360)
  const dayInYear = ((day - 1) % 360) + 1
  const month = Math.ceil(dayInYear / 30)
  const dayInMonth = ((dayInYear - 1) % 30) + 1

  return `Year ${year}, Month ${month}, Day ${dayInMonth}`
}

/**
 * Short format: "Day 45"
 */
export function formatGameDayShort(day: number): string {
  if (day <= 0) return 'Day 0'
  return `Day ${day}`
}

/**
 * Effective end of an expedition. An early retreat keeps its planned
 * `return_day`; `actual_return_day` records when the party really came home.
 * Returns the day to display, the days actually spent, and whether the plan broke.
 */
export function expeditionEnd(
  startDay: number,
  returnDay: number,
  actualReturnDay?: number | null,
): { day: number; days: number; early: boolean } {
  const early = actualReturnDay != null && actualReturnDay !== returnDay
  const day = early ? actualReturnDay : returnDay
  return { day, days: day - startDay + 1, early }
}
