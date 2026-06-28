/**
 * useAssistant — React Query mutation for AI summarization.
 *
 * Why a mutation and not a query?
 * Summarization is a POST with side effects (persists to ai_logs).
 * Queries are for idempotent GETs. Mutations handle loading/error/data
 * lifecycle identically — and give us onSuccess/onError callbacks.
 */
import toast from 'react-hot-toast'
import { assistantApi } from '@/services/api'
import { useMutation } from '@tanstack/react-query'
import type { SummarizeRequest, SummarizeResponse } from '@/types/transaction.types'

export function useSummarize() {
  return useMutation<SummarizeResponse, Error, SummarizeRequest>({
    mutationFn: (payload) => assistantApi.summarize(payload),

    onSuccess: (data) => {
      const label = data.is_mock ? '🤖 Mock' : '✨ OpenAI'
      toast.success(`Summary ready — ${label} · ${data.tokens_used} tokens`, {
        duration: 4000,
      })
    },

    onError: (error) => {
      toast.error(`Summarization failed: ${error.message}`)
    },
  })
}
