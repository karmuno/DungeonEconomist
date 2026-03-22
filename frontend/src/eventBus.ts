import mitt from 'mitt'

type Events = {
  'game-events': Array<{ type: string; message: string; expedition_id?: number | null; first_time?: boolean }>
  'refresh-dashboard': void
}

const eventBus = mitt<Events>()

export default eventBus