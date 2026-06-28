/**
 * Root Zustand store.
 *
 * Uses the slice pattern: each slice owns its state and actions.
 * The root store composes them. This scales cleanly — adding a new
 * feature slice doesn't touch existing slices.
 *
 * Why Zustand over Redux?
 * - No boilerplate (no action creators, no reducers, no selectors setup)
 * - React Query handles server state; Zustand handles UI state only
 * - Devtools support built-in
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import {
  createTransactionSlice,
  type TransactionSlice,
} from './slices/transactionSlice'
import {
  createNotificationSlice,
  type NotificationSlice,
} from './slices/notificationSlice'

export type AppStore = TransactionSlice & NotificationSlice

export const useAppStore = create<AppStore>()(
  devtools(
    (set) => ({
      ...createTransactionSlice(set as Parameters<typeof createTransactionSlice>[0]),
      ...createNotificationSlice(set as Parameters<typeof createNotificationSlice>[0]),
    }),
    { name: 'TransactionDashboard' }
  )
)

// ── Typed selectors ────────────────────────────────────────────────────────────
// Memoized selectors prevent unnecessary re-renders
export const selectLiveTransactions = (s: AppStore) =>
  Object.values(s.liveTransactions).sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  )

export const selectEvents = (s: AppStore) => s.events
export const selectWsStatus = (s: AppStore) => s.wsStatus
