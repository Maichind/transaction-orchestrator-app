/**
 * AssistantPanel — demo UI for the /assistant/summarize endpoint.
 *
 * Shows:
 * - Text input for the content to summarize
 * - Source badge: "OpenAI gpt-4o-mini" vs "Mock"
 * - Token count (cost visibility)
 * - The summary output in a styled card
 *
 * Integrated into the Dashboard below the transaction list.
 */
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '../atoms/button'
import { Spinner } from '../atoms/spinner'
import { useSummarize } from '@/hooks/useAssistant'

export function AssistantPanel() {
  const [text, setText] = useState('')
  const summarize = useSummarize()

  const handleSubmit = () => {
    if (text.trim().length < 10) return
    summarize.mutate({ text: text.trim() })
  }

  const charCount = text.length
  const isValid = charCount >= 10 && charCount <= 8000

  return (
    <section className="bg-surface border border-border rounded-xl p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-primary flex items-center gap-2">
          <span className="text-purple-400">✦</span> AI Summarizer
        </h2>
        <span className="text-2xs font-mono text-tertiary">
          POST /assistant/summarize
        </span>
      </div>

      {/* Input */}
      <div className="space-y-1.5">
        <label
          htmlFor="summarize-input"
          className="text-xs font-medium text-secondary uppercase tracking-wider"
        >
          Text to summarize
        </label>
        <textarea
          id="summarize-input"
          rows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste any text here — a Wikipedia paragraph, a news article, a transaction note…"
          className={cn(
            'w-full bg-overlay border border-border rounded px-3 py-2',
            'text-sm text-primary placeholder:text-tertiary font-sans',
            'focus:outline-none focus:ring-1 focus:ring-accent/60 focus:border-accent/60',
            'resize-none transition-colors',
            !isValid && charCount > 0 && 'border-failed/40'
          )}
        />
        <div className="flex justify-between items-center">
          <span className={cn(
            'text-2xs font-mono',
            charCount > 8000 ? 'text-failed' : 'text-tertiary'
          )}>
            {charCount} / 8000 chars
          </span>
          {charCount < 10 && charCount > 0 && (
            <span className="text-2xs text-failed">Minimum 10 characters</span>
          )}
        </div>
      </div>

      {/* Submit */}
      <Button
        onClick={handleSubmit}
        loading={summarize.isPending}
        disabled={!isValid}
        className="w-full"
      >
        Summarize
      </Button>

      {/* Result */}
      {summarize.isPending && (
        <div className="flex items-center gap-3 py-4 text-secondary">
          <Spinner size="md" />
          <span className="text-sm">Generating summary…</span>
        </div>
      )}

      {summarize.isSuccess && summarize.data && (
        <div className="space-y-3 animate-fade-in">
          {/* Meta badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className={cn(
              'inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-2xs font-mono',
              summarize.data.is_mock
                ? 'text-pending bg-pending/10 border-pending/30'
                : 'text-processed bg-processed/10 border-processed/30'
            )}>
              <span className="w-1.5 h-1.5 rounded-full bg-current" />
              {summarize.data.is_mock ? 'Mock response' : `OpenAI ${summarize.data.model}`}
            </span>

            {!summarize.data.is_mock && (
              <span className="text-2xs font-mono text-tertiary">
                {summarize.data.tokens_used} tokens
              </span>
            )}

            <span className="text-2xs font-mono text-tertiary">
              id: {summarize.data.id.slice(0, 8)}
            </span>
          </div>

          {/* Summary output */}
          <div className="bg-overlay border border-border/60 rounded-lg p-4">
            <p className="text-sm text-primary leading-relaxed">
              {summarize.data.summary}
            </p>
          </div>

          {/* Cost note */}
          {summarize.data.is_mock && (
            <p className="text-2xs text-tertiary">
              ℹ️ No <code className="font-mono bg-overlay px-1 rounded">OPENAI_API_KEY</code> configured —
              set it in <code className="font-mono bg-overlay px-1 rounded">.env</code> to use real GPT-4o-mini.
            </p>
          )}
        </div>
      )}

      {summarize.isError && (
        <div className="bg-failed/10 border border-failed/30 rounded-lg p-3 text-sm text-failed">
          {summarize.error.message}
        </div>
      )}
    </section>
  )
}
