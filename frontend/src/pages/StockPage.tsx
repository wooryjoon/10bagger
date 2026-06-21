import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { ArrowLeft, TrendingUp, TrendingDown, Banknote, Newspaper, Activity } from 'lucide-react'
import { api } from '@/lib/api'
import type { Stock, PricePoint, Period, ScoreBreakdown } from '@/types'

const PERIODS: { label: string; value: Period }[] = [
  { label: '1주', value: '1w' },
  { label: '1달', value: '1m' },
  { label: '3달', value: '3m' },
  { label: '6달', value: '6m' },
  { label: '1년', value: '1y' },
]

// ── Category definitions ──────────────────────────────────────────────────────

type CategoryDef = {
  id: string
  label: string
  sublabel: string
  description: string
  icon: React.ElementType
  color: string
  bg: string
  weight: string
  keys: string[]
}

const CATEGORIES: CategoryDef[] = [
  {
    id: 'fundamental',
    label: '펀더멘탈',
    sublabel: '재무 건전성',
    description: '기업이 실제로 돈을 잘 버는가',
    icon: Banknote,
    color: '#0066FF',
    bg: '#EEF4FF',
    weight: '50%',
    keys: ['safety', 'fcf_yield', 'liquidity', 'accruals', 'quality_growth', 'shareholder_yield'],
  },
  {
    id: 'narrative',
    label: '시장 내러티브',
    sublabel: '테마 & 전문가 전망',
    description: '지금 시장이 주목하는 종목인가',
    icon: Newspaper,
    color: '#7C3AED',
    bg: '#F5F3FF',
    weight: '30%',
    keys: ['keyword_match', 'consensus'],
  },
  {
    id: 'technical',
    label: '기술적 분석',
    sublabel: '차트 & 모멘텀',
    description: '차트 패턴이 매수 타이밍을 가리키는가',
    icon: Activity,
    color: '#D97706',
    bg: '#FFFBEB',
    weight: '20%',
    keys: ['ma_convergence', 'volume_explosion', 'relative_strength'],
  },
]

const METRIC_DETAIL: Record<string, { label: string; hint: string }> = {
  safety:             { label: '연속 흑자',        hint: '영업이익·현금흐름 2년 이상 흑자' },
  fcf_yield:          { label: '현금 창출력',       hint: '시총 대비 잉여현금흐름 수익률' },
  liquidity:          { label: '유동비율',           hint: '유동자산/유동부채 — 1.2x 이상이면 단기 안전' },
  accruals:           { label: '이익 품질',          hint: '현금 이익 > 회계 이익이면 이익 조작 가능성 낮음' },
  quality_growth:     { label: '성장 품질',          hint: '매출채권·재고 증가율이 매출 증가율 이하면 건전' },
  shareholder_yield:  { label: '주주환원 수익률',    hint: '배당 수익률 + 자사주 매입 수익률 합산' },
  keyword_match:      { label: '시장 테마',          hint: '현재 핫한 테마 섹터 해당 여부' },
  consensus:          { label: '애널리스트 목표가',  hint: '전문가 평균 목표가 업사이드' },
  ma_convergence:     { label: '이평선·BB 수렴',     hint: '20/60/120일선 수렴 + 볼린저 밴드 폭 최저 → 이탈 임박' },
  volume_explosion:   { label: '거래량 급증',        hint: '최근 5일 이례적 대량거래 발생 여부' },
  relative_strength:  { label: '상대 강도',          hint: 'NASDAQ 대비 3개월 수익률 초과 여부' },
}

function getCategoryInsight(id: string, pct: number): string {
  if (id === 'fundamental') {
    if (pct >= 70) return '재무 건전성 우수 — 안정적인 현금 창출력을 보유 중입니다.'
    if (pct >= 40) return '기본 재무 요건은 충족하나 일부 개선 여지가 있습니다.'
    return '재무 리스크에 주의가 필요합니다.'
  }
  if (id === 'narrative') {
    if (pct >= 70) return '현재 시장에서 가장 주목받는 테마 섹터에 속합니다.'
    if (pct >= 40) return '일부 시장 트렌드와 연관성이 있습니다.'
    return '현재 시장 핵심 테마와 거리가 있습니다.'
  }
  if (id === 'technical') {
    if (pct >= 70) return '차트상 강한 매수 신호가 감지됩니다.'
    if (pct >= 40) return '차트 신호가 혼재되어 있습니다.'
    return '현재 차트 신호는 매수에 불리합니다.'
  }
  return ''
}

function scoreColor(pct: number): string {
  if (pct >= 0.7) return '#22C55E'
  if (pct >= 0.4) return '#F59E0B'
  return '#EF4444'
}

function fmt(val: number | null | undefined, decimals = 1, suffix = '') {
  if (val == null) return '—'
  return val.toFixed(decimals) + suffix
}

// ── Circular score gauge ──────────────────────────────────────────────────────

function CircleScore({ pct, color }: { pct: number; color: string }) {
  const r = 26
  const circ = 2 * Math.PI * r
  const dash = (Math.min(pct, 100) / 100) * circ
  return (
    <div className="relative w-17 h-17 flex items-center justify-center shrink-0">
      <svg className="absolute inset-0 -rotate-90" width={68} height={68}>
        <circle cx={34} cy={34} r={r} stroke="#E8EAED" strokeWidth={6} fill="none" />
        <circle cx={34} cy={34} r={r} stroke={color} strokeWidth={6} fill="none"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
      </svg>
      <div className="relative flex flex-col items-center leading-none">
        <span className="text-base font-bold tabular-nums" style={{ color }}>{Math.round(pct)}</span>
        <span className="text-[9px] text-[#B0B8C1]">/ 100</span>
      </div>
    </div>
  )
}

// ── Category card ─────────────────────────────────────────────────────────────

function CategoryCard({ cat, breakdown }: { cat: CategoryDef; breakdown: ScoreBreakdown }) {
  const Icon = cat.icon

  const totalScore = cat.keys.reduce((s, k) => s + (breakdown[k]?.score ?? 0), 0)
  const totalMax = cat.keys.reduce((s, k) => s + (breakdown[k]?.max ?? 0), 0)
  const pct = totalMax > 0 ? (totalScore / totalMax) * 100 : 0
  const col = scoreColor(pct / 100)
  const levelLabel = pct >= 70 ? '우수' : pct >= 40 ? '보통' : '미흡'

  return (
    <div className="border border-[#E8EAED] rounded-2xl overflow-hidden shadow-sm">
      {/* ── Header with colored background ── */}
      <div style={{ background: cat.bg }} className="px-5 pt-5 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
              style={{ background: cat.color }}>
              <Icon size={22} color="white" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-base font-bold text-[#191F28]">{cat.label}</span>
                <span className="text-[11px] font-semibold text-white px-2 py-0.5 rounded-full"
                  style={{ background: cat.color }}>
                  {cat.weight} 반영
                </span>
              </div>
              <p className="text-xs text-[#8B95A1] mt-0.5">{cat.description}</p>
            </div>
          </div>
          <CircleScore pct={pct} color={col} />
        </div>

        {/* Level badge + insight */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-[11px] font-bold text-white px-2.5 py-0.5 rounded-full"
            style={{ background: col }}>
            {levelLabel}
          </span>
          <span className="text-xs text-[#8B95A1]">{getCategoryInsight(cat.id, pct)}</span>
        </div>
      </div>

      {/* ── Sub-metric bars ── */}
      <div className="px-5 py-4 space-y-3.5 bg-white">
        {cat.keys.map(key => {
          const item = breakdown[key]
          if (!item) return null
          const detail = METRIC_DETAIL[key]
          const itemPct = item.score / item.max
          const barColor = scoreColor(itemPct)
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-[#191F28]">{detail?.label ?? key}</span>
                  <span className="text-[11px] text-[#B0B8C1]">{detail?.hint}</span>
                </div>
                <span className="text-xs font-bold tabular-nums ml-2 shrink-0"
                  style={{ color: barColor }}>
                  {item.score}/{item.max}
                </span>
              </div>
              <div className="h-1.5 bg-[#F2F4F6] rounded-full overflow-hidden">
                <div className="h-1.5 rounded-full transition-all"
                  style={{ width: `${itemPct * 100}%`, background: barColor }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Price chart ───────────────────────────────────────────────────────────────

function PriceChart({ history, isUp }: { history: PricePoint[]; isUp: boolean }) {
  const color = isUp ? '#F04452' : '#1570EF'
  const formatted = history.map((p) => ({ ...p, dateLabel: p.date.slice(5) }))
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={formatted} margin={{ top: 8, right: 4, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.15} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#F2F4F6" vertical={false} />
        <XAxis dataKey="dateLabel" tick={{ fontSize: 11, fill: '#B0B8C1' }}
          axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 11, fill: '#B0B8C1' }} axisLine={false} tickLine={false}
          width={56} tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v.toFixed(0)}
          domain={['auto', 'auto']} />
        <Tooltip
          contentStyle={{ border: '1px solid #E8EAED', borderRadius: 10, boxShadow: '0 4px 16px rgba(0,0,0,0.08)', fontSize: 12 }}
          labelStyle={{ color: '#191F28', fontWeight: 600, marginBottom: 2 }}
          formatter={(v) => [(v as number).toFixed(2), '종가']}
        />
        <Area type="monotone" dataKey="close" stroke={color} strokeWidth={2}
          fill="url(#priceGrad)" dot={false} activeDot={{ r: 4, fill: color, strokeWidth: 0 }} />
      </AreaChart>
    </ResponsiveContainer>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#F9FAFB] rounded-xl p-4 border border-[#E8EAED]">
      <p className="text-xs text-[#8B95A1] mb-1.5">{label}</p>
      <p className="text-xl font-bold text-[#191F28] tabular-nums">{value}</p>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function StockPage() {
  const { ticker } = useParams<{ ticker: string }>()
  const decodedTicker = decodeURIComponent(ticker!)
  const navigate = useNavigate()

  const [stock, setStock] = useState<Stock | null>(null)
  const [history, setHistory] = useState<PricePoint[]>([])
  const [period, setPeriod] = useState<Period>('1m')
  // 'loading' = initial DB fetch, 'analyzing' = on-demand analysis, 'error' | 'ok'
  const [status, setStatus] = useState<'loading' | 'analyzing' | 'error' | 'ok'>('loading')
  const [historyLoading, setHistoryLoading] = useState(false)

  useEffect(() => {
    setStatus('loading')
    Promise.all([
      api.getStock(decodedTicker),
      api.getHistory(decodedTicker, period),
    ])
      .then(([s, h]) => { setStock(s); setHistory(h); setStatus('ok') })
      .catch((e: Error) => {
        if (e.message.includes('404')) {
          // Ticker not in DB — run real-time analysis
          setStatus('analyzing')
          api.getHistory(decodedTicker, period).then(setHistory).catch(() => {})
          api.analyzeStock(decodedTicker)
            .then(s => { setStock(s); setStatus('ok') })
            .catch(() => setStatus('error'))
        } else {
          setStatus('error')
        }
      })
  }, [decodedTicker])

  useEffect(() => {
    if (!stock) return
    setHistoryLoading(true)
    api.getHistory(decodedTicker, period)
      .then(setHistory)
      .finally(() => setHistoryLoading(false))
  }, [period, decodedTicker, stock])

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#0066FF] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (status === 'analyzing') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-5 text-center px-6">
          <div className="w-16 h-16 rounded-2xl bg-[#EEF4FF] flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-[#0066FF] border-t-transparent rounded-full animate-spin" />
          </div>
          <div>
            <p className="text-lg font-bold text-[#191F28] mb-1">
              {decodedTicker} 실시간 분석 중...
            </p>
            <p className="text-sm text-[#8B95A1]">
              재무제표 · 시장 테마 · 차트를 종합 분석하고 있습니다
            </p>
            <p className="text-xs text-[#B0B8C1] mt-2">약 20~30초 소요됩니다</p>
          </div>
          <div className="flex gap-1.5 mt-2">
            {['재무 건전성', '시장 내러티브', '기술적 분석'].map((step, i) => (
              <span key={step} className="text-xs px-3 py-1 rounded-full border border-[#E8EAED] text-[#8B95A1]"
                style={{ animationDelay: `${i * 0.3}s` }}>
                {step}
              </span>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (status === 'error' || !stock) {
    return (
      <div className="min-h-screen flex items-center justify-center flex-col gap-3">
        <p className="text-[#8B95A1]">종목을 찾을 수 없습니다. 티커 심볼을 확인해 주세요.</p>
        <button onClick={() => navigate(-1)} className="text-[#0066FF] text-sm font-medium">← 돌아가기</button>
      </div>
    )
  }

  const m = stock.data
  const priceChange = history.length >= 2
    ? (history[history.length - 1].close - history[0].close) / history[0].close * 100
    : 0
  const isUp = priceChange >= 0

  const isKospi = stock.market === 'kospi'
  const priceStr = m.current_price != null
    ? (isKospi
        ? m.current_price.toLocaleString('ko-KR') + '원'
        : '$' + m.current_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }))
    : '—'

  const scoreCol = stock.score >= 70 ? '#0066FF' : stock.score >= 50 ? '#6B8FE8' : '#B0B8C1'

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-white border-b border-[#E8EAED]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-2 sm:gap-4 h-14 overflow-hidden">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-1.5 text-[#8B95A1] hover:text-[#191F28] transition-colors text-sm font-medium shrink-0"
            >
              <ArrowLeft size={16} />
              뒤로
            </button>
            <div className="h-4 w-px bg-[#E8EAED] shrink-0" />
            <div className="flex items-baseline gap-1.5 sm:gap-2 min-w-0 overflow-hidden">
              <span className="text-sm font-bold text-[#191F28] shrink-0">{stock.ticker.replace(/^KS/, '')}</span>
              <span className="text-xs text-[#8B95A1] truncate">{stock.name}</span>
            </div>
            <span className="ml-auto shrink-0 text-xs bg-[#F2F4F6] text-[#8B95A1] px-2.5 py-1 rounded-full font-medium hidden sm:block">
              {stock.sector}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Price section */}
        <div className="flex items-end justify-between flex-wrap gap-y-4">
          <div>
            <p className="text-3xl font-bold text-[#191F28] tabular-nums">{priceStr}</p>
            <div className={`flex items-center gap-1.5 mt-1.5 text-sm font-semibold ${isUp ? 'text-[#F04452]' : 'text-[#1570EF]'}`}>
              {isUp ? <TrendingUp size={15} /> : <TrendingDown size={15} />}
              {isUp ? '+' : ''}{priceChange.toFixed(2)}% ({PERIODS.find(p => p.value === period)?.label})
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-[#8B95A1] mb-1">저평가 점수</p>
            <p className="text-3xl font-bold tabular-nums" style={{ color: scoreCol }}>
              {Math.round(stock.score)}
              <span className="text-base font-normal text-[#B0B8C1]">/100</span>
            </p>
          </div>
        </div>

        {/* Chart — ticker/name shown at top */}
        <div className="border border-[#E8EAED] rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
            <div className="flex items-baseline gap-2">
              <span className="text-base font-bold text-[#191F28]">{stock.ticker.replace(/^KS/, '')}</span>
              <span className="text-sm text-[#8B95A1]">{stock.name}</span>
            </div>
            <div className="flex gap-1">
              {PERIODS.map(({ label, value }) => (
                <button
                  key={value}
                  onClick={() => setPeriod(value)}
                  className={`px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-semibold rounded-xl transition-all ${
                    period === value
                      ? 'bg-[#191F28] text-white'
                      : 'text-[#8B95A1] hover:text-[#191F28] hover:bg-[#F2F4F6]'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className={historyLoading ? 'opacity-50 transition-opacity' : 'transition-opacity'}>
            {history.length > 0
              ? <PriceChart history={history} isUp={isUp} />
              : <div className="h-64 flex items-center justify-center text-[#B0B8C1] text-sm">차트 데이터 없음</div>
            }
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MetricCard label="P/E 비율" value={fmt(m.pe_ratio, 1, 'x')} />
          <MetricCard label="P/B 비율" value={fmt(m.pb_ratio, 2, 'x')} />
          <MetricCard label="ROE" value={m.roe != null ? fmt(m.roe * 100, 1, '%') : '—'} />
          <MetricCard label="영업이익률" value={m.operating_margin != null ? fmt(m.operating_margin * 100, 1, '%') : '—'} />
          <MetricCard label="EV/EBITDA" value={fmt(m.ev_ebitda, 1, 'x')} />
          <MetricCard label="부채비율" value={fmt(m.debt_to_equity, 0, '%')} />
          <MetricCard label="매출성장률" value={m.revenue_growth != null ? fmt(m.revenue_growth * 100, 1, '%') : '—'} />
          <MetricCard label="EPS성장률" value={m.earnings_growth != null ? fmt(m.earnings_growth * 100, 1, '%') : '—'} />
        </div>

        {/* Undervaluation analysis — 3 category cards */}
        <div>
          <h2 className="text-base font-bold text-[#191F28] mb-4">저평가 근거 분석</h2>
          <div className="space-y-4">
            {CATEGORIES.map(cat => (
              <CategoryCard key={cat.id} cat={cat} breakdown={stock.score_breakdown} />
            ))}
          </div>
        </div>

        {/* 52w range */}
        {(m.week52_high != null || m.week52_low != null) && (
          <div className="border border-[#E8EAED] rounded-2xl p-6 shadow-sm">
            <h2 className="text-base font-bold text-[#191F28] mb-4">52주 가격 범위</h2>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-[#8B95A1]">52주 최저</span>
              <span className="text-[#8B95A1]">52주 최고</span>
            </div>
            <div className="flex items-center justify-between font-bold text-[#191F28] tabular-nums mb-3">
              <span>{m.week52_low != null ? (isKospi ? m.week52_low.toLocaleString() + '원' : '$' + m.week52_low.toFixed(2)) : '—'}</span>
              <span>{m.week52_high != null ? (isKospi ? m.week52_high.toLocaleString() + '원' : '$' + m.week52_high.toFixed(2)) : '—'}</span>
            </div>
            {m.week52_low != null && m.week52_high != null && m.current_price != null && (
              <div className="relative h-1.5 bg-[#F2F4F6] rounded-full">
                <div
                  className="absolute top-0 left-0 h-1.5 bg-[#0066FF] rounded-full"
                  style={{
                    width: `${Math.min(100, Math.max(0, (m.current_price - m.week52_low) / (m.week52_high - m.week52_low) * 100))}%`
                  }}
                />
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
