import mitt from 'mitt'

type Events = {
  'game-events': Array<{ type: string; message: string; expedition_id?: number | null; first_time?: boolean; event_subtype?: string | null; adventurers?: Array<{ id: number; name: string }> }>
  'refresh-dashboard': void
  'toggle-metrics': void
  'toggle-metrics-button': void
}

const eventBus = mitt<Events>()

export default eventBus