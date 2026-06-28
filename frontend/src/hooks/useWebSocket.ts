/**
 * useWebSocket — connects the WS service to the app store.
 *
 * On every incoming event:
 * 1. Push to the notification feed (store)
 * 2. Upsert/update the live transaction map (store)
 * 3. Invalidate React Query cache so the list re-fetches (server state sync)
 *
 * Mounted once at App level — single WS connection for the whole app.
 */
import toast from 'react-hot-toast'
import { useEffect, useRef } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { formatAmount, formatId } from '@/lib/utils'
import { useQueryClient } from '@tanstack/react-query'
import type { WSEvent } from '@/types/transaction.types'
import { createWSConnection, type WSHandle } from '@/services/websocket'

export function useWebSocket(): void {
  const queryClient = useQueryClient()
  const wsRef = useRef<WSHandle | null>(null)

  const pushEvent = useAppStore((s) => s.pushEvent)
  const setWsStatus = useAppStore((s) => s.setWsStatus)
  const upsertTransaction = useAppStore((s) => s.upsertTransaction)
  const updateTransactionStatus = useAppStore((s) => s.updateTransactionStatus)

  useEffect(() => {
    wsRef.current = createWSConnection({
      onStatusChange: setWsStatus,

      onMessage: (event: WSEvent) => {
        // 1. Always push to notification feed
        pushEvent(event)

        // 2. Handle by event type
        if (event.event === 'transaction.created') {
          const { id, user_id, amount, status } = event.payload

          // Optimistic: add to live map immediately
          upsertTransaction({
            id,
            user_id,
            amount,
            status,
            type: 'credit', // will be corrected by next query invalidation
            idempotency_key: null,
            task_id: null,
            error_message: null,
            created_at: event.timestamp ?? new Date().toISOString(),
            updated_at: event.timestamp ?? new Date().toISOString(),
          })

          // Invalidate list so it re-fetches with correct full data
          void queryClient.invalidateQueries({ queryKey: ['transactions'] })

          toast.success(
            `New ${status} transaction — ${formatAmount(amount)} (${formatId(id)})`,
            { duration: 4000, icon: '💳' }
          )
        }

        if (event.event === 'transaction.status_changed') {
          const { id, new_status, old_status, error_message } = event.payload

          updateTransactionStatus(id, new_status, error_message)
          void queryClient.invalidateQueries({ queryKey: ['transactions'] })
          void queryClient.invalidateQueries({ queryKey: ['transaction', id] })

          const icon =
            new_status === 'processed' ? '✅' :
            new_status === 'failed'    ? '❌' : '⏳'

          toast(
            `Transaction ${formatId(id)}: ${old_status} → ${new_status}`,
            { icon, duration: 5000 }
          )
        }
      },
    })

    return () => {
      wsRef.current?.disconnect()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}
