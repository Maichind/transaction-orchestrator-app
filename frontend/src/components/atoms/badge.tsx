/**
 * Atomic UI component.
 * These have no business logic — pure presentational primitives.
 */
import { cn } from '@/lib/utils'
import { STATUS_COLORS, STATUS_DOT } from '@/lib/utils'
import type { TransactionStatus } from '@/types/transaction.types'

// ── Badge ──────────────────────────────────────────────────────────────────────
interface BadgeProps {
  status: TransactionStatus
  className?: string
}

export function StatusBadge({ status, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-2xs font-mono font-medium uppercase tracking-wider',
        STATUS_COLORS[status],
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full', STATUS_DOT[status],
        status === 'pending' && 'animate-pulse-dot'
      )} />
      {status}
    </span>
  )
}
