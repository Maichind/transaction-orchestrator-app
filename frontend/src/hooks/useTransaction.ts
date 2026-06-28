/**
 * React Query hooks — server state for transactions.
 *
 * Why React Query over raw fetch in components?
 * - Automatic caching, background refetch, stale-while-revalidate
 * - Loading/error states without manual useState
 * - Query invalidation syncs WS updates with server truth
 * - DevTools for inspection during demo
 */
import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query'
import type {
  TransactionCreate,
  Transaction,
  TransactionListResponse,
} from '@/types/transaction.types'
import toast from 'react-hot-toast'
import { transactionApi } from '@/services/api'
import { useAppStore } from '@/store/useAppStore'
import { generateIdempotencyKey } from '@/lib/utils'

// ── Query keys ─────────────────────────────────────────────────────────────────
export const txKeys = {
  all:    ['transactions'] as const,
  list:   (params: object) => ['transactions', 'list', params] as const,
  detail: (id: string) => ['transaction', id] as const,
}

// ── List transactions ──────────────────────────────────────────────────────────
export function useTransactionList(limit = 20, offset = 0) {
  return useQuery<TransactionListResponse>({
    queryKey: txKeys.list({ limit, offset }),
    queryFn: () => transactionApi.list({ limit, offset }),
    placeholderData: keepPreviousData,
    staleTime: 10_000,   // 10s — WS keeps us updated; no need to over-fetch
    refetchOnWindowFocus: true,
  })
}

// ── Single transaction ─────────────────────────────────────────────────────────
export function useTransaction(id: string) {
  return useQuery<Transaction>({
    queryKey: txKeys.detail(id),
    queryFn: () => transactionApi.getById(id),
    staleTime: 5_000,
  })
}

// ── Create transaction ─────────────────────────────────────────────────────────
export function useCreateTransaction() {
  const queryClient = useQueryClient()
  const upsertTransaction = useAppStore((s) => s.upsertTransaction)

  return useMutation<Transaction, Error, TransactionCreate>({
    mutationFn: (payload) => {
      const key = payload.idempotency_key ?? generateIdempotencyKey()
      return transactionApi.create(payload, key)
    },

    onSuccess: (data) => {
      // Optimistically add to live map
      upsertTransaction(data)
      // Invalidate list query
      void queryClient.invalidateQueries({ queryKey: txKeys.all })
      toast.success('Transaction created successfully', { icon: '✅' })
    },

    onError: (error) => {
      toast.error(error.message, { duration: 6000 })
    },
  })
}

// ── Async process transaction ──────────────────────────────────────────────────
export function useAsyncProcess() {
  const queryClient = useQueryClient()

  return useMutation<
    { task_id: string; transaction_id: string },
    Error,
    string
  >({
    mutationFn: (transactionId: string) =>
      transactionApi.asyncProcess({ transaction_id: transactionId }),

    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: txKeys.all })
      toast.success(`Task enqueued: ${data.task_id.slice(0, 8)}`, {
        icon: '⚙️',
        duration: 4000,
      })
    },

    onError: (error) => {
      toast.error(error.message)
    },
  })
}
