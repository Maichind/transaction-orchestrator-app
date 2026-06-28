/**
 * Atomic UI component.
 * These have no business logic — pure presentational primitives.
 */
import { cn } from '@/lib/utils'
import { Spinner } from './spinner'
import { type ButtonHTMLAttributes } from 'react'

// ── Button ─────────────────────────────────────────────────────────────────────
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger'
  size?: 'sm' | 'md'
  loading?: boolean
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  const base = 'inline-flex items-center justify-center gap-2 rounded font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 disabled:opacity-40 disabled:cursor-not-allowed'

  const variants = {
    primary: 'bg-accent hover:bg-accent-hover text-white shadow-glow-accent',
    ghost:   'bg-transparent hover:bg-overlay text-secondary hover:text-primary border border-border',
    danger:  'bg-failed/10 hover:bg-failed/20 text-failed border border-failed/30',
  }

  const sizes = {
    sm: 'text-xs px-3 py-1.5',
    md: 'text-sm px-4 py-2',
  }

  return (
    <button
      className={cn(base, variants[variant], sizes[size], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  )
}
