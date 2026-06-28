/**
 * App root.
 *
 * Provider order matters:
 * 1. QueryClientProvider — React Query cache
 * 2. Toaster            — toast notifications (needs to be outside pages)
 * 3. WebSocket hook     — single WS connection for the whole app
 * 4. Dashboard          — page content
 */
import { Toaster } from 'react-hot-toast'
import { Dashboard } from '@/pages/Dashboard'
import { useWebSocket } from '@/hooks/useWebSocket'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 10_000,
    },
    mutations: {
      retry: 0,
    },
  },
})

// Isolated component so useWebSocket runs inside QueryClientProvider
// (it needs useQueryClient for cache invalidation)
function AppInner() {
  useWebSocket()
  return <Dashboard />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#1F2937',
            color: '#F9FAFB',
            border: '1px solid #374151',
            fontFamily: 'Inter, sans-serif',
            fontSize: '13px',
          },
          success: { iconTheme: { primary: '#10B981', secondary: '#111827' } },
          error:   { iconTheme: { primary: '#EF4444', secondary: '#111827' } },
        }}
      />
      <AppInner />
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}
