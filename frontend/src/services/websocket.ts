/**
 * WebSocket client factory with auto-reconnect.
 *
 * Reconnection strategy: exponential backoff with jitter
 *   attempt 1 → 1s, attempt 2 → 2s, attempt 3 → 4s … max 30s
 *   jitter: ±20% to prevent thundering herd on server restart
 *
 * Why a factory function instead of a class?
 * - Easier to test (just call the function, get back control handles)
 * - No `this` binding issues in callbacks
 * - Composable with the Zustand store without lifecycle concerns
 */
import type { WSEvent } from '@/types/transaction.types'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface WSOptions {
  onMessage: (event: WSEvent) => void
  onStatusChange: (status: WSStatus) => void
  maxRetries?: number
}

export interface WSHandle {
  disconnect: () => void
}

const MAX_BACKOFF_MS = 30_000
const BASE_BACKOFF_MS = 1_000

function getBackoffMs(attempt: number): number {
  const exponential = Math.min(BASE_BACKOFF_MS * 2 ** attempt, MAX_BACKOFF_MS)
  const jitter = exponential * (0.8 + Math.random() * 0.4) // ±20%
  return Math.floor(jitter)
}

export function createWSConnection(options: WSOptions): WSHandle {
  const { onMessage, onStatusChange, maxRetries = 10 } = options

  let ws: WebSocket | null = null
  let attempt = 0
  let intentionallyClosed = false
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function connect(): void {
    if (intentionallyClosed) return

    onStatusChange('connecting')
    ws = new WebSocket(`${WS_URL}/transactions/stream`)

    ws.onopen = () => {
      attempt = 0
      onStatusChange('connected')
    }

    ws.onmessage = (ev) => {
      try {
        const event = JSON.parse(ev.data) as WSEvent
        onMessage(event)
      } catch {
        // Malformed JSON — ignore gracefully
      }
    }

    ws.onerror = () => {
      onStatusChange('error')
    }

    ws.onclose = () => {
      if (intentionallyClosed) {
        onStatusChange('disconnected')
        return
      }

      onStatusChange('disconnected')

      if (attempt >= maxRetries) {
        console.warn('[WS] Max retries reached. Giving up.')
        return
      }

      const delay = getBackoffMs(attempt)
      attempt++
      console.info(`[WS] Reconnecting in ${delay}ms (attempt ${attempt}/${maxRetries})`)
      reconnectTimer = setTimeout(connect, delay)
    }
  }

  connect()

  return {
    disconnect: () => {
      intentionallyClosed = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      ws?.close()
    },
  }
}
