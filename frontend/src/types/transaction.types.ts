// Mirror of backend schemas — single source of truth for the frontend
// If backend DTOs change, update here first. 
export type TransactionType = 'credit' | 'debit' | 'transfer'
export type TransactionStatus = 'pending' | 'processed' | 'failed'

export interface Transaction {
  id: string
  user_id: string
  amount: string
  type: TransactionType
  status: TransactionStatus
  idempotency_key: string | null
  task_id: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface TransactionCreate {
  user_id: string
  amount: string
  type: TransactionType
  idempotency_key?: string
}

export interface AsyncProcessRequest {
  transaction_id: string
}

export interface AsyncProcessResponse {
  transaction_id: string
  task_id: string
  status: TransactionStatus
  message: string
}

export interface TransactionListResponse {
  items: Transaction[]
  total: number
  limit: number
  offset: number
}


// ── WebSocket event shapes ───────────────────────────────────────────────────── 
export type WSEventType =
  | 'connected'
  | 'transaction.created'
  | 'transaction.status_changed'
  | 'ping'
 
export interface WSEventBase {
  event: WSEventType
  timestamp?: string
}
 
export interface WSConnectedEvent extends WSEventBase {
  event: 'connected'
  message: string
  active_connections: number
}
 
export interface WSTransactionCreatedEvent extends WSEventBase {
  event: 'transaction.created'
  payload: {
    id: string
    user_id: string
    amount: string
    status: TransactionStatus
  }
}
 
export interface WSTransactionStatusChangedEvent extends WSEventBase {
  event: 'transaction.status_changed'
  payload: {
    id: string
    user_id: string
    old_status: TransactionStatus
    new_status: TransactionStatus
    task_id: string | null
    error_message: string | null
  }
}

export interface WSPingEvent extends WSEventBase {
  event: 'ping'
}

export type WSEvent =
  | WSConnectedEvent
  | WSTransactionCreatedEvent
  | WSTransactionStatusChangedEvent
  | WSPingEvent


// ── AI / Assistant ───────────────────────────────────────────────────────────── 
export interface SummarizeRequest {
  text: string
}

export interface SummarizeResponse {
  id: string
  summary: string
  model: string
  tokens_used: number
  source: 'openai' | 'mock'
  is_mock: boolean
  created_at: string
}
