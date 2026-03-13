/**
 * Format gold/silver/copper into a display string like "2gp 3sp 5cp".
 * Omits zero denominations. Returns "0cp" if all are zero.
 */
export function formatCurrency(gold: number, silver: number, copper: number): string {
  const parts: string[] = []
  if (gold > 0) parts.push(`${gold}gp`)
  if (silver > 0) parts.push(`${silver}sp`)
  if (copper > 0) parts.push(`${copper}cp`)
  return parts.length > 0 ? parts.join(' ') : '0cp'
}
