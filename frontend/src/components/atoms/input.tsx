/**
 * Atomic UI component.
 * These have no business logic — pure presentational primitives.
 */
import { cn } from '@/lib/utils'
import { type InputHTMLAttributes, forwardRef } from 'react'

// ── Input ──────────────────────────────────────────────────────────────────────
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={inputId} className="text-xs font-medium text-secondary uppercase tracking-wider">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'bg-overlay border border-border rounded px-3 py-2 text-sm text-primary placeholder:text-tertiary',
            'focus:outline-none focus:ring-1 focus:ring-accent/60 focus:border-accent/60',
            'transition-colors font-mono',
            error && 'border-failed/60 focus:ring-failed/40',
            className
          )}
          {...props}
        />
        {error && <p className="text-2xs text-failed">{error}</p>}
      </div>
    )
  }
)
Input.displayName = 'Input'
