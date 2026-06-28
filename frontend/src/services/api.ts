/**
 * HTTP API service layer.
 *
 * Design decisions:
 * - Axios over fetch: interceptors, automatic JSON, better error objects
 * - All methods are typed with the shared types — no `any` in callers
 * - Base URL from env var → works identically in dev (proxy) and prod (direct)
 */
import axios, { type AxiosInstance, type AxiosError } from 'axios'
import type {
  Transaction,
  TransactionCreate,
  AsyncProcessRequest,
  AsyncProcessResponse,
  TransactionListResponse,
  SummarizeRequest,
  SummarizeResponse,
} from '@/types/transaction.types'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── Axios instance ─────────────────────────────────────────────────────────────
const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// ── Request interceptor: attach idempotency key if present ────────────────────
http.interceptors.request.use((config) => {
  return config
})

// ── Response interceptor: normalize errors ────────────────────────────────────
http.interceptors.response.use(
  (res) => res,
  (error: AxiosError<{ detail: string }>) => {
    const message =
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)

// ── Transaction API ────────────────────────────────────────────────────────────
export const transactionApi = {
  create: async (
    payload: TransactionCreate,
    idempotencyKey?: string
  ): Promise<Transaction> => {
    const headers = idempotencyKey
      ? { 'Idempotency-Key': idempotencyKey }
      : {}
    const { data } = await http.post<Transaction>(
      '/transactions/create',
      payload,
      { headers }
    )
    return data
  },

  asyncProcess: async (
    payload: AsyncProcessRequest
  ): Promise<AsyncProcessResponse> => {
    const { data } = await http.post<AsyncProcessResponse>(
      '/transactions/async-process',
      payload
    )
    return data
  },

  list: async (params?: {
    limit?: number
    offset?: number
  }): Promise<TransactionListResponse> => {
    const { data } = await http.get<TransactionListResponse>('/transactions', {
      params,
    })
    return data
  },

  getById: async (id: string): Promise<Transaction> => {
    const { data } = await http.get<Transaction>(`/transactions/${id}`)
    return data
  },
}

// ── Assistant API ──────────────────────────────────────────────────────────────
export const assistantApi = {
  summarize: async (payload: SummarizeRequest): Promise<SummarizeResponse> => {
    const { data } = await http.post<SummarizeResponse>(
      '/assistant/summarize',
      payload
    )
    return data
  },
}
