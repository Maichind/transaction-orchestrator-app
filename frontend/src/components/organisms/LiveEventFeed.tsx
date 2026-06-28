import { useRef, useEffect } from 'react'
import { Button } from '../atoms/button'
import { WSStatusDot } from '../atoms/ws_status'
import { WSEventRow } from '@/components/molecules/WSEventRow'
import { useAppStore, selectEvents, selectWsStatus } from '@/store/useAppStore'

export function LiveEventFeed() {
  const events    = useAppStore(selectEvents)
  const wsStatus  = useAppStore(selectWsStatus)
  const clearEvents = useAppStore((s) => s.clearEvents)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to newest event (prepended at top — no scroll needed)
  // But keep scroll position stable if user scrolled up
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Only auto-scroll if user is near the top (newest events)
    if (containerRef.current && containerRef.current.scrollTop < 40) {
      containerRef.current.scrollTop = 0
    }
  }, [events.length])

  const nonPingEvents = events.filter((e) => e.event.event !== 'ping')

  return (
    <aside className="flex flex-col h-full bg-surface border border-border rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-semibold text-primary uppercase tracking-widest">
            Live Feed
          </h2>
          <WSStatusDot status={wsStatus} />
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-2xs text-tertiary">
            {nonPingEvents.length} events
          </span>
          <Button size="sm" variant="ghost" onClick={clearEvents}>
            Clear
          </Button>
        </div>
      </div>

      {/* Terminal body */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto px-4 py-3 space-y-0.5 font-mono"
        style={{ scrollbarWidth: 'thin', scrollbarColor: '#374151 transparent' }}
      >
        {events.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-tertiary">
            <div className="w-8 h-8 border border-border rounded-full flex items-center justify-center">
              <span className="text-lg">∅</span>
            </div>
            <p className="text-2xs">Waiting for events…</p>
          </div>
        )}

        {events.map((entry) => (
          <WSEventRow key={entry.id} entry={entry} />
        ))}

        <div ref={bottomRef} />
      </div>

      {/* Footer: connection hint */}
      <div className="px-4 py-2 border-t border-border/50 shrink-0">
        <p className="font-mono text-2xs text-tertiary truncate">
          ws://localhost:8000/transactions/stream
        </p>
      </div>
    </aside>
  )
}
