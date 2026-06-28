import { useState } from 'react'
import { Button } from '../atoms/button'
import { Spinner } from '../atoms/spinner'
import { useTransactionList } from '@/hooks/useTransaction'
import { TransactionCard } from '@/components/molecules/TransactionCard'
import { useAppStore, selectLiveTransactions } from '@/store/useAppStore'

const PAGE_SIZE = 10

export function TransactionList() {
  const [offset, setOffset] = useState(0)
  const { data, isLoading, isError, refetch, isFetching } = useTransactionList(PAGE_SIZE, offset)
  const liveTransactions = useAppStore(selectLiveTransactions)

  // Merge: live WS transactions on top, server list below (deduplicated by id)
  const serverIds = new Set(data?.items.map((t) => t.id) ?? [])
  const liveFeed = liveTransactions.filter((t) => !serverIds.has(t.id))

  const allItems = [...liveFeed, ...(data?.items ?? [])]

  return (
    <section>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-primary flex items-center gap-2">
          Transactions
          {isFetching && !isLoading && (
            <Spinner size="sm" />
          )}
        </h2>
        <div className="flex items-center gap-2">
          {data && (
            <span className="text-2xs text-tertiary font-mono">
              {data.total} total
            </span>
          )}
          <Button size="sm" variant="ghost" onClick={() => void refetch()}>
            Refresh
          </Button>
        </div>
      </div>

      {/* States */}
      {isLoading && (
        <div className="flex items-center justify-center py-12 text-secondary">
          <Spinner size="lg" />
        </div>
      )}

      {isError && (
        <div className="bg-failed/10 border border-failed/30 rounded-lg p-4 text-sm text-failed">
          Failed to load transactions. Check that the API is running.
          <Button size="sm" variant="danger" onClick={() => void refetch()} className="mt-2">
            Retry
          </Button>
        </div>
      )}

      {!isLoading && allItems.length === 0 && (
        <div className="text-center py-12 text-tertiary">
          <p className="text-sm">No transactions yet.</p>
          <p className="text-2xs mt-1">Create one above to get started.</p>
        </div>
      )}

      {/* List */}
      <div className="space-y-2">
        {liveFeed.map((tx) => (
          <TransactionCard key={tx.id} transaction={tx} isLive />
        ))}
        {data?.items.map((tx) => (
          <TransactionCard key={tx.id} transaction={tx} />
        ))}
      </div>

      {/* Pagination */}
      {data && data.total > PAGE_SIZE && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
          <Button
            size="sm"
            variant="ghost"
            disabled={offset === 0}
            onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
          >
            ← Previous
          </Button>
          <span className="text-2xs text-tertiary font-mono">
            {offset + 1}–{Math.min(offset + PAGE_SIZE, data.total)} of {data.total}
          </span>
          <Button
            size="sm"
            variant="ghost"
            disabled={offset + PAGE_SIZE >= data.total}
            onClick={() => setOffset((o) => o + PAGE_SIZE)}
          >
            Next →
          </Button>
        </div>
      )}
    </section>
  )
}
