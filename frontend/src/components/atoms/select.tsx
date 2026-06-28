/**
 * Atomic UI component.
 * These have no business logic — pure presentational primitives.
 */
import { cn } from '@/lib/utils'
import { type InputHTMLAttributes } from 'react'

// ── Select ─────────────────────────────────────────────────────────────────────
interface SelectProps extends InputHTMLAttributes<HTMLSelectElement> {
  label: string
  options: { value: string; label: string }[]
  error?: string
}

export function Select({ label, options, error, className, id, ...props }: SelectProps) {
  const selectId = id ?? label.toLowerCase().replace(/\s+/g, '-')
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={selectId} className="text-xs font-medium text-secondary uppercase tracking-wider">
        {label}
      </label>
      <select
        id={selectId}
        className={cn(
          'bg-overlay border border-border rounded px-3 py-2 text-sm text-primary',
          'focus:outline-none focus:ring-1 focus:ring-accent/60 focus:border-accent/60',
          'transition-colors appearance-none cursor-pointer',
          error && 'border-failed/60',
          className
        )}
        {...(props as object)}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-2xs text-failed">{error}</p>}
    </div>
  )
}
