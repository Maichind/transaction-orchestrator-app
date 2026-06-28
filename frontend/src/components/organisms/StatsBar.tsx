import { useMemo } from 'react'
import { formatAmount } from '@/lib/utils'
import { useTransactionList } from '@/hooks/useTransaction'
import type { TransactionStatus } from '@/types/transaction.types'

interface StatCardProps {
  label: string
  value: string | number
  sub?: string
  accent?: string
}

function StatCard({ label, value, sub, accent = 'text-primary' }: StatCardProps) {
  return (
    <div className="bg-surface border border-border rounded-lg px-4 py-3 flex flex-col gap-0.5">
      <span className="text-2xs text-tertiary uppercase tracking-wider font-medium">{label}</span>
      <span className={`font-mono text-xl font-semibold ${accent}`}>{value}</span>
      {sub && <span className="text-2xs text-tertiary font-mono">{sub}</span>}
    </div>
  )
}

export function StatsBar() {
  const { data } = useTransactionList(100, 0)

  const stats = useMemo(() => {
    const items = data?.items ?? []
    const byStatus = items.reduce<Record<TransactionStatus, number>>(
      (acc, t) => { acc[t.status]++; return acc },
      { pending: 0, processed: 0, failed: 0 }
    )
    const totalVolume = items.reduce((sum, t) => sum + parseFloat(t.amount), 0)
    const successRate = items.length
      ? Math.round((byStatus.processed / items.length) * 100)
      : 0

    return { byStatus, totalVolume, successRate, total: items.length }
  }, [data])

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <StatCard label="Total" value={stats.total} sub="transactions" />
      <StatCard
        label="Processed"
        value={stats.byStatus.processed}
        sub={`${stats.successRate}% success rate`}
        accent="text-processed"
      />
      <StatCard
        label="Pending"
        value={stats.byStatus.pending}
        sub="awaiting processing"
        accent="text-pending"
      />
      <StatCard
        label="Volume"
        value={formatAmount(stats.totalVolume)}
        sub="total USD"
        accent="text-accent"
      />
    </div>
  )
}
