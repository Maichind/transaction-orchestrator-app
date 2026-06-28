import { cn, formatAmount, formatId } from '@/lib/utils'
import type { NotificationEntry } from '@/store/slices/notificationSlice'

interface WSEventRowProps {
  entry: NotificationEntry
}

export function WSEventRow({ entry }: WSEventRowProps) {
  const { event, receivedAt } = entry
  const time = new Date(receivedAt).toLocaleTimeString('en-US', { hour12: false })

  if (event.event === 'ping') {
    return (
      <div className="flex items-center gap-2 font-mono text-2xs text-tertiary py-0.5 opacity-50">
        <span className="text-tertiary">{time}</span>
        <span>·</span>
        <span>ping</span>
      </div>
    )
  }

  if (event.event === 'connected') {
    return (
      <div className="flex items-center gap-2 font-mono text-2xs py-0.5 animate-slide-in">
        <span className="text-tertiary">{time}</span>
        <span className="text-processed">●</span>
        <span className="text-processed">connected</span>
        <span className="text-tertiary">· {event.active_connections} client(s)</span>
      </div>
    )
  }

  if (event.event === 'transaction.created') {
    const { id, amount, status, user_id } = event.payload
    return (
      <div className="flex items-start gap-2 font-mono text-2xs py-0.5 animate-slide-in">
        <span className="text-tertiary shrink-0">{time}</span>
        <span className="text-event-created">+</span>
        <div className="flex flex-wrap gap-x-2 gap-y-0.5">
          <span className="text-event-created">txn.created</span>
          <span className="text-primary">{formatId(id)}</span>
          <span className={cn(
            amount && Number(amount) > 0 ? 'text-processed' : 'text-secondary'
          )}>
            {formatAmount(amount)}
          </span>
          <span className="text-tertiary">{user_id}</span>
          <span className="text-pending">[{status}]</span>
        </div>
      </div>
    )
  }

  if (event.event === 'transaction.status_changed') {
    const { id, old_status, new_status, error_message } = event.payload
    const statusColor =
      new_status === 'processed' ? 'text-processed' :
      new_status === 'failed'    ? 'text-failed' : 'text-pending'

    return (
      <div className="flex items-start gap-2 font-mono text-2xs py-0.5 animate-slide-in">
        <span className="text-tertiary shrink-0">{time}</span>
        <span className="text-event-changed">↻</span>
        <div className="flex flex-wrap gap-x-2 gap-y-0.5">
          <span className="text-event-changed">txn.status</span>
          <span className="text-primary">{formatId(id)}</span>
          <span className="text-tertiary">{old_status}</span>
          <span className="text-tertiary">→</span>
          <span className={statusColor}>{new_status}</span>
          {error_message && (
            <span className="text-failed truncate max-w-[160px]" title={error_message}>
              {error_message.slice(0, 30)}…
            </span>
          )}
        </div>
      </div>
    )
  }

  return null
}
