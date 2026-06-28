import type { WSEvent } from '@/types/transaction.types'

export interface NotificationEntry {
  id: string
  event: WSEvent
  receivedAt: string
}

export interface NotificationSlice {
  events: NotificationEntry[]
  wsStatus: 'connecting' | 'connected' | 'disconnected' | 'error'

  pushEvent: (event: WSEvent) => void
  setWsStatus: (status: NotificationSlice['wsStatus']) => void
  clearEvents: () => void
}

const MAX_EVENTS = 100 // keep feed from growing unbounded

export const createNotificationSlice = (
  set: (fn: (state: NotificationSlice) => Partial<NotificationSlice>) => void
): NotificationSlice => ({
  events: [],
  wsStatus: 'connecting',

  pushEvent: (event) =>
    set((state) => ({
      events: [
        {
          id: `${Date.now()}-${Math.random()}`,
          event,
          receivedAt: new Date().toISOString(),
        },
        ...state.events,
      ].slice(0, MAX_EVENTS),
    })),

  setWsStatus: (wsStatus) => set(() => ({ wsStatus })),

  clearEvents: () => set(() => ({ events: [] })),
})
