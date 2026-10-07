import mitt from 'mitt'
import type { DashboardStats } from './types'

type Events = {
  'game-events': Array<{ type: string; message: string; expedition_id?: number | null; first_time?: boolean; event_subtype?: string | null; adventurers?: Array<{ id: number; name: string }> }>
  'refresh-dashboard': void
  'dashboard-data': DashboardStats
  'toggle-metrics': void
  'toggle-metrics-button': void
}

const eventBus = mitt<Events>()

export default eventBus