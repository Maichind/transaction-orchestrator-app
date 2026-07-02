import { WSStatusDot } from '@/components/atoms/ws_status'
import { StatsBar } from '@/components/organisms/StatsBar'
import { useAppStore, selectWsStatus } from '@/store/useAppStore'
import { LiveEventFeed } from '@/components/organisms/LiveEventFeed'
import { AssistantPanel } from '@/components/organisms/AssistantPanel'
import { TransactionList } from '@/components/organisms/TransactionList'
import { CreateTransactionForm } from '@/components/organisms/CreateTransactionForm'

export function Dashboard() {
  const wsStatus = useAppStore(selectWsStatus)

  return (
    <div className="min-h-screen bg-void flex flex-col">
      {/* ── Top bar ──────────────────────────────────────────────────────────── */}
      <header className="border-b border-border/60 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          {/* Logo mark */}
          <div className="w-6 h-6 rounded bg-accent/20 border border-accent/40 flex items-center justify-center">
            <span className="text-accent text-xs font-bold font-mono">T</span>
          </div>
          <span className="text-sm font-semibold text-primary tracking-tight">
            Transaction Dashboard
          </span>
          <span className="text-tertiary text-xs font-mono hidden sm:block">
            v1.0.0
          </span>
        </div>

        <div className="flex items-center gap-4">
          <WSStatusDot status={wsStatus} />
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-2xs text-tertiary hover:text-secondary font-mono transition-colors"
          >
            API Docs ↗
          </a>
          <a
            href="http://localhost:5555"
            target="_blank"
            rel="noopener noreferrer"
            className="text-2xs text-tertiary hover:text-secondary font-mono transition-colors"
          >
            Flower ↗
          </a>
        </div>
      </header>

      {/* ── Main content ─────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col lg:flex-row gap-0 overflow-hidden">
        {/* ── Left panel: controls + list ────────────────────────────────────── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
            {/* Stats row */}
            <StatsBar />

            {/* Create form */}
            <CreateTransactionForm />

            {/* Transaction list */}
            <TransactionList />

            {/* AI Summarizer */}
            <AssistantPanel />
          </div>
        </div>

        {/* ── Right panel: live WS feed ───────────────────────────────────────── */}
        <div className="
          lg:w-[380px] xl:w-[420px]
          h-[320px] lg:h-auto
          border-t lg:border-t-0 lg:border-l border-border/60
          flex flex-col px-6 py-5 overflow-hidden
          shrink-0
        ">
          <LiveEventFeed />
        </div>
      </main>

      {/* ── Footer ───────────────────────────────────────────────────────────── */}
      <footer className="border-t border-border/40 px-6 py-2 flex items-center justify-between shrink-0">
        <span className="text-2xs text-tertiary font-mono">
          FastAPI · Celery · Redis · WebSocket · OpenAI
        </span>
        <span className="text-2xs text-tertiary font-mono">
          Technical Assessment — 2024
        </span>
      </footer>
    </div>
  )
}
