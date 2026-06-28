import { useState } from 'react'
import { Button } from '../atoms/button'
import { StatusBadge } from '../atoms/badge'
import { useAsyncProcess } from '@/hooks/useTransaction'
import type { Transaction } from '@/types/transaction.types'
import { cn, formatAmount, formatDate, formatId, TYPE_COLORS, TYPE_LABELS } from '@/lib/utils'

interface TransactionCardProps {
  transaction: Transaction
  isLive?: boolean
}

export function TransactionCard({ transaction: tx, isLive = false }: TransactionCardProps) {
  const [expanded, setExpanded] = useState(false)
  const asyncProcess = useAsyncProcess()

  return (
    <article
      className={cn(
        'bg-surface border border-border rounded-lg p-4 transition-all duration-200',
        'hover:border-accent/30 hover:shadow-glow-accent',
        isLive && 'animate-slide-in border-accent/20'
      )}
    >
      {/* Main row */}
      <div className="flex items-center gap-3">
        {/* Amount + type */}
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-lg font-semibold text-primary">
              {formatAmount(tx.amount)}
            </span>
            <span className={cn('text-xs font-medium', TYPE_COLORS[tx.type])}>
              {TYPE_LABELS[tx.type]}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="font-mono text-2xs text-tertiary">{formatId(tx.id)}</span>
            <span className="text-tertiary text-2xs">·</span>
            <span className="text-2xs text-secondary">{tx.user_id}</span>
          </div>
        </div>

        {/* Status + date */}
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <StatusBadge status={tx.status} />
          <span className="font-mono text-2xs text-tertiary">
            {formatDate(tx.created_at)}
          </span>
        </div>

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-tertiary hover:text-secondary transition-colors ml-1"
          aria-label={expanded ? 'Collapse details' : 'Expand details'}
        >
          <svg
            className={cn('w-4 h-4 transition-transform', expanded && 'rotate-180')}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-border/60 space-y-2 animate-fade-in">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-2xs font-mono">
            <span className="text-tertiary">Full ID</span>
            <span className="text-secondary truncate">{tx.id}</span>
            {tx.task_id && (
              <>
                <span className="text-tertiary">Task ID</span>
                <span className="text-secondary truncate">{tx.task_id.slice(0, 20)}…</span>
              </>
            )}
            {tx.idempotency_key && (
              <>
                <span className="text-tertiary">Idempotency Key</span>
                <span className="text-secondary">{tx.idempotency_key}</span>
              </>
            )}
            {tx.error_message && (
              <>
                <span className="text-tertiary">Error</span>
                <span className="text-failed">{tx.error_message}</span>
              </>
            )}
          </div>

          {/* Enqueue for processing */}
          {tx.status === 'pending' && !tx.task_id && (
            <Button
              size="sm"
              variant="ghost"
              loading={asyncProcess.isPending}
              onClick={() => asyncProcess.mutate(tx.id)}
              className="mt-2"
            >
              ⚙️ Process async
            </Button>
          )}
        </div>
      )}
    </article>
  )
}
