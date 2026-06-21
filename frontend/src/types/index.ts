export interface StockMetrics {
  name: string
  sector: string
  industry: string
  market_cap: number | null
  current_price: number | null
  pe_ratio: number | null
  forward_pe: number | null
  pb_ratio: number | null
  ev_ebitda: number | null
  roe: number | null
  roa: number | null
  operating_margin: number | null
  profit_margin: number | null
  revenue_growth: number | null
  earnings_growth: number | null
  debt_to_equity: number | null
  current_ratio: number | null
  dividend_yield: number | null
  week52_high: number | null
  week52_low: number | null
  beta: number | null
}

export interface ScoreBreakdownItem {
  score: number
  max: number
  value: number | null
  sector_avg?: number | null
}

export type ScoreBreakdown = Record<string, ScoreBreakdownItem>

export interface Stock {
  ticker: string
  market: 'nasdaq' | 'kospi'
  name: string
  sector: string
  industry: string
  data: StockMetrics
  score: number
  score_breakdown: ScoreBreakdown
  reasoning: string
  updated_at: string
}

export interface PricePoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export type Market = 'nasdaq' | 'kospi'
export type Period = '1w' | '1m' | '3m' | '6m' | '1y'
