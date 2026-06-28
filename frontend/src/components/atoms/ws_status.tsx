/**
 * Atomic UI component.
 * These have no business logic — pure presentational primitives.
 */
import { cn } from '@/lib/utils'

// ── WS Status Indicator ────────────────────────────────────────────────────────
type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export function WSStatusDot({ status }: { status: WSStatus }) {
  const config = {
    connected:    { color: 'bg-processed', label: 'Live', pulse: true },
    connecting:   { color: 'bg-pending',   label: 'Connecting…', pulse: true },
    disconnected: { color: 'bg-tertiary',  label: 'Disconnected', pulse: false },
    error:        { color: 'bg-failed',    label: 'Error', pulse: false },
  }[status]

  return (
    <span className="inline-flex items-center gap-1.5 text-2xs text-secondary font-mono">
      <span className={cn(
        'w-1.5 h-1.5 rounded-full',
        config.color,
        config.pulse && 'animate-pulse-dot'
      )} />
      {config.label}
    </span>
  )
}
