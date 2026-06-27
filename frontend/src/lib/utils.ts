import { clsx, type ClassValue } from 'clsx'
import { format, formatDistanceToNow } from 'date-fns'
import type { TransactionStatus, TransactionType } from '@/types/transaction.types'

// ── Class merging ──────────────────────────────────────────────────────────────
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs)
}

// ── Formatting ─────────────────────────────────────────────────────────────────
export function formatAmount(amount: string | number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(Number(amount))
}

export function formatDate(dateStr: string): string {
  return format(new Date(dateStr), 'MMM d, HH:mm:ss')
}

export function formatRelative(dateStr: string): string {
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
}

export function formatId(id: string): string {
  return id.slice(0, 8).toUpperCase()
}

// ── Status helpers ─────────────────────────────────────────────────────────────
export const STATUS_COLORS: Record<TransactionStatus, string> = {
  pending:   'text-pending  bg-pending/10  border-pending/30',
  processed: 'text-processed bg-processed/10 border-processed/30',
  failed:    'text-failed   bg-failed/10   border-failed/30',
}

export const STATUS_DOT: Record<TransactionStatus, string> = {
  pending:   'bg-pending',
  processed: 'bg-processed',
  failed:    'bg-failed',
}

export const TYPE_LABELS: Record<TransactionType, string> = {
  credit:   'Credit',
  debit:    'Debit',
  transfer: 'Transfer',
}

export const TYPE_COLORS: Record<TransactionType, string> = {
  credit:   'text-processed',
  debit:    'text-failed',
  transfer: 'text-accent',
}

// ── Idempotency key generator ──────────────────────────────────────────────────
export function generateIdempotencyKey(prefix = 'txn'): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}
