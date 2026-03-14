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
