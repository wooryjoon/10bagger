import type { Stock, PricePoint, Market, Period } from '@/types'

const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8080').trim()

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    cache: 'no-store',
    headers: { 'ngrok-skip-browser-warning': 'true' },
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json()
}

export interface SnapshotInfo {
  collected_at: string
  stock_count: number
  history_count: number
}

export interface StatusResponse {
  nasdaq_stocks: number
  kospi_stocks: number
  snapshots: {
    nasdaq: SnapshotInfo | null
    kospi: SnapshotInfo | null
  }
}

export interface RunLogEntry {
  ts: string
  market: string
  status: 'success' | 'failed'
  stocks: number
  duration_sec: number
  error: string | null
}

export const api = {
  getStatus: () => get<StatusResponse>('/api/status'),
  getRunLog: () => get<RunLogEntry[]>('/api/run-log'),
  getSectors: (market: Market) => get<Record<string, Stock[]>>(`/api/sectors?market=${market}`),
  getStock: (ticker: string) => get<Stock>(`/api/stocks/${encodeURIComponent(ticker)}`),
  getHistory: (ticker: string, period: Period) =>
    get<PricePoint[]>(`/api/stocks/${encodeURIComponent(ticker)}/history?period=${period}`),
  analyzeStock: (ticker: string) => get<Stock>(`/api/analyze/${encodeURIComponent(ticker)}`),
  getTopPick: (market: Market) => get<Stock>(`/api/top-pick?market=${market}`),
  getStocks: (market: Market, limit = 200) => get<Stock[]>(`/api/stocks?market=${market}&limit=${limit}`),
  getSwing: () => get<Stock[]>('/api/swing'),
}
