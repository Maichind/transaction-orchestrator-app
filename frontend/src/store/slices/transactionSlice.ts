import type { Transaction, TransactionStatus } from '@/types/transaction.types'

export interface TransactionSlice {
  // Live transaction map — keyed by ID for O(1) updates
  liveTransactions: Record<string, Transaction>

  // Actions
  upsertTransaction: (tx: Transaction) => void
  updateTransactionStatus: (
    id: string,
    status: TransactionStatus,
    errorMessage?: string | null
  ) => void
  clearLiveTransactions: () => void
}

export const createTransactionSlice = (
  set: (fn: (state: TransactionSlice) => Partial<TransactionSlice>) => void
): TransactionSlice => ({
  liveTransactions: {},

  upsertTransaction: (tx) =>
    set((state) => ({
      liveTransactions: {
        ...state.liveTransactions,
        [tx.id]: tx,
      },
    })),

  updateTransactionStatus: (id, status, errorMessage) =>
    set((state) => {
      const existing = state.liveTransactions[id]
      if (!existing) return {}
      return {
        liveTransactions: {
          ...state.liveTransactions,
          [id]: {
            ...existing,
            status,
            error_message: errorMessage ?? existing.error_message,
            updated_at: new Date().toISOString(),
          },
        },
      }
    }),

  clearLiveTransactions: () => set(() => ({ liveTransactions: {} })),
})
