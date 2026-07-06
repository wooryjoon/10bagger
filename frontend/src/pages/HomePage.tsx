import { useState, useEffect, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { TrendingDown, Clock, AlertCircle, Search, Sparkles } from "lucide-react";
import { api, type StatusResponse } from "@/lib/api";
import type { Stock, Market } from "@/types";

const SECTOR_KO: Record<string, string> = {
  Technology: "기술",
  "Communication Services": "커뮤니케이션",
  "Consumer Cyclical": "소비재(경기)",
  "Consumer Defensive": "소비재(필수)",
  Healthcare: "헬스케어",
  Financials: "금융",
  "Financial Services": "금융서비스",
  Industrials: "산업재",
  Energy: "에너지",
  "Basic Materials": "소재",
  "Real Estate": "부동산",
  Utilities: "유틸리티",
  Unknown: "기타",
};

function fmt(val: number | null | undefined, decimals = 1, suffix = "") {
  if (val == null) return "—";
  return val.toFixed(decimals) + suffix;
}

function fmtPrice(val: number | null | undefined, market: Market) {
  if (val == null) return "—";
  return market === "kospi"
    ? val.toLocaleString("ko-KR") + "원"
    : "$" +
        val.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
}

function fmtDatetime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("ko-KR", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function isStale(iso: string | null | undefined): boolean {
  if (!iso) return true;
  return Date.now() - new Date(iso).getTime() > 25 * 60 * 60 * 1000; // > 25h
}

function enhanced(s: Stock): number {
  return (s.score ?? 0) + (s.stage5_score ?? 0);
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? "#0066FF" : score >= 50 ? "#6B8FE8" : "#B0B8C1";
  return (
    <div className="flex items-center gap-2">
      <div className="w-14 h-1.5 rounded-full bg-[#F2F4F6] overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${score}%`, background: color }}
        />
      </div>
      <span className="text-sm font-bold tabular-nums" style={{ color }}>
        {Math.round(score)}
      </span>
    </div>
  );
}

function StockRow({ rank, stock }: { rank: number; stock: Stock }) {
  const navigate = useNavigate();
  const m = stock.data;
  return (
    <tr
      onClick={() => navigate(`/stock/${encodeURIComponent(stock.ticker)}`)}
      className="border-b border-[#F2F4F6] last:border-0 hover:bg-[#F9FAFB] cursor-pointer transition-colors"
    >
      <td className="px-3 sm:px-5 py-2.5 sm:py-3.5 text-sm text-[#B0B8C1] tabular-nums">
        {rank}
      </td>
      <td className="px-2 sm:px-4 py-2.5 sm:py-3.5">
        <div className="flex flex-col">
          <span className="text-sm font-bold text-[#191F28] tracking-tight">
            {stock.ticker.replace(/^KS/, "")}
          </span>
          <span className="text-xs text-[#8B95A1] mt-0.5 truncate max-w-25 sm:max-w-40">
            {stock.name}
          </span>
        </div>
      </td>
      <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm font-medium text-[#191F28] tabular-nums">
        {fmtPrice(m.current_price, stock.market)}
      </td>
      <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm text-[#191F28] tabular-nums hidden sm:table-cell">
        {fmt(m.pe_ratio, 1, "x")}
      </td>
      <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm text-[#191F28] tabular-nums hidden sm:table-cell">
        {fmt(m.pb_ratio, 2, "x")}
      </td>
      <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm text-[#191F28] tabular-nums hidden md:table-cell">
        {m.roe != null ? fmt(m.roe * 100, 1, "%") : "—"}
      </td>
      <td className="px-2 sm:px-4 py-2.5 sm:py-3.5">
        <div className="flex items-center gap-1.5">
          <ScoreBar score={enhanced(stock)} />
          {stock.investment_tier && (
            <span
              className="text-[10px] font-bold text-white px-1.5 py-0.5 rounded shrink-0"
              style={{
                background: stock.investment_tier === 1 ? '#D97706'
                  : stock.investment_tier === 2 ? '#0066FF'
                  : '#6B7280',
              }}
            >
              T{stock.investment_tier}
            </span>
          )}
        </div>
      </td>
      <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs text-[#8B95A1] max-w-55 hidden lg:table-cell">
        <span className="line-clamp-2">{stock.reasoning}</span>
      </td>
    </tr>
  );
}

function Tier1Section({ sectors }: { sectors: Record<string, Stock[]> }) {
  const navigate = useNavigate();
  const stocks = Object.values(sectors)
    .flat()
    .filter((s) => s.investment_tier === 1)
    .sort((a, b) => enhanced(b) - enhanced(a));

  if (stocks.length === 0) return null;

  return (
    <section>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-base font-bold text-[#191F28]">Tier 1 핵심 종목</span>
        <span className="text-xs font-bold text-white bg-[#D97706] px-2 py-0.5 rounded-full">
          {stocks.length}종목
        </span>
        <span className="text-xs text-[#8B95A1]">· 4단계 스크리닝 최상위</span>
      </div>
      <div className="border border-[#FDE68A] rounded-2xl overflow-hidden shadow-sm bg-[#FFFBEB]/40">
        <table className="w-full">
          <thead>
            <tr className="bg-[#FFFBEB] border-b border-[#FDE68A]">
              <th className="px-3 sm:px-5 py-3 text-left text-xs font-medium text-[#B0B8C1]">#</th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1]">종목</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1]">현재가</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden sm:table-cell">P/E</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden sm:table-cell">P/B</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden md:table-cell">ROE</th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1]">점수</th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1] hidden lg:table-cell">저평가 근거</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((s, i) => (
              <tr
                key={s.ticker}
                onClick={() => navigate(`/stock/${encodeURIComponent(s.ticker)}`)}
                className="border-b border-[#FEF3C7] last:border-0 hover:bg-[#FEF9EE] cursor-pointer transition-colors"
              >
                <td className="px-3 sm:px-5 py-2.5 sm:py-3.5 text-sm text-[#B0B8C1] tabular-nums">{i + 1}</td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5">
                  <div className="flex flex-col">
                    <span className="text-sm font-bold text-[#191F28] tracking-tight">{s.ticker}</span>
                    <span className="text-xs text-[#8B95A1] mt-0.5 truncate max-w-25 sm:max-w-40">{s.name}</span>
                  </div>
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm font-medium text-[#191F28] tabular-nums">
                  {fmtPrice(s.data.current_price, s.market)}
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm text-[#191F28] tabular-nums hidden sm:table-cell">
                  {fmt(s.data.pe_ratio, 1, "x")}
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm text-[#191F28] tabular-nums hidden sm:table-cell">
                  {fmt(s.data.pb_ratio, 2, "x")}
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm text-[#191F28] tabular-nums hidden md:table-cell">
                  {s.data.roe != null ? fmt(s.data.roe * 100, 1, "%") : "—"}
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5">
                  <ScoreBar score={enhanced(s)} />
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs text-[#8B95A1] max-w-55 hidden lg:table-cell">
                  <span className="line-clamp-2">{s.reasoning}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SectorTable({ sector, stocks }: { sector: string; stocks: Stock[] }) {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-base font-bold text-[#191F28]">
            {SECTOR_KO[sector] ?? sector}
          </span>
          <span className="text-xs text-[#8B95A1] bg-[#F2F4F6] px-2 py-0.5 rounded-full">
            {sector}
          </span>
        </div>
        <span className="text-xs text-[#B0B8C1]">{stocks.length}종목</span>
      </div>
      <div className="border border-[#E8EAED] rounded-2xl overflow-hidden shadow-sm">
        <table className="w-full">
          <thead>
            <tr className="bg-[#F9FAFB] border-b border-[#E8EAED]">
              <th className="px-3 sm:px-5 py-3 text-left text-xs font-medium text-[#B0B8C1]">
                #
              </th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1]">
                종목
              </th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1]">
                현재가
              </th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden sm:table-cell">
                P/E
              </th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden sm:table-cell">
                P/B
              </th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden md:table-cell">
                ROE
              </th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1]">
                점수
              </th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1] hidden lg:table-cell">
                저평가 근거
              </th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((s, i) => (
              <StockRow key={s.ticker} rank={i + 1} stock={s} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}


function LastUpdatedBadge({
  snapshot,
}: {
  snapshot: StatusResponse["snapshots"]["nasdaq"];
}) {
  if (!snapshot) {
    return (
      <span className="flex items-center gap-1.5 text-xs text-[#B0B8C1]">
        <AlertCircle size={12} />
        미수집
      </span>
    );
  }
  const stale = isStale(snapshot.collected_at);
  return (
    <span
      className={`flex items-center gap-1.5 text-xs ${stale ? "text-[#F04452]" : "text-[#8B95A1]"}`}
    >
      <Clock size={12} />
      {fmtDatetime(snapshot.collected_at)} 기준
      {stale && " (오래된 데이터)"}
    </span>
  );
}

function TickerSearch({ className }: { className?: string }) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const submit = () => {
    const t = query.trim().toUpperCase();
    if (t) navigate(`/stock/${encodeURIComponent(t)}`);
  };

  return (
    <div
      className={`flex items-center gap-1 bg-[#F2F4F6] rounded-xl px-3 py-1.5 ${className ?? ""}`}
    >
      <Search size={13} className="text-[#B0B8C1] shrink-0" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        placeholder="티커 검색  IREN, NVDA…"
        className="bg-transparent text-sm text-[#191F28] placeholder-[#B0B8C1] outline-none flex-1 min-w-0 w-28 sm:w-40"
      />
      {query && (
        <button
          onClick={submit}
          className="text-[11px] font-bold text-white bg-[#0066FF] px-2 py-0.5 rounded-lg shrink-0"
        >
          분석
        </button>
      )}
    </div>
  );
}

function TopPickCard({ stock }: { stock: Stock }) {
  const navigate = useNavigate();
  const scoreCol =
    enhanced(stock) >= 75 ? "#22C55E" : enhanced(stock) >= 65 ? "#F59E0B" : "#6B8FE8";
  const reasonParts = stock.reasoning.split(" · ").slice(0, 3);

  return (
    <div className="relative overflow-hidden rounded-2xl bg-[#0A0F1C] px-6 py-5 shadow-lg">
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-64 h-40 rounded-full bg-[#0066FF]/10 blur-3xl pointer-events-none" />

      <div className="relative flex items-start justify-between gap-4 flex-wrap">
        {/* Left: question + ticker */}
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold text-[#6B9FFF] uppercase tracking-widest mb-2">
            딱 하나만 산다면?
          </p>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-2xl font-extrabold text-white">
              {stock.ticker}
            </span>
            <span className="text-sm text-[#8B95A1] truncate">
              {stock.name}
            </span>
          </div>
          <span className="inline-block text-xs text-[#8B95A1] bg-white/5 border border-white/10 px-2.5 py-0.5 rounded-full">
            {stock.sector}
          </span>

          {/* Reasons */}
          <ul className="mt-3 space-y-1">
            {reasonParts.map((r, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs text-[#8B95A1]"
              >
                <span className="mt-0.5 w-1 h-1 rounded-full bg-[#6B9FFF] shrink-0" />
                {r}
              </li>
            ))}
          </ul>
        </div>

        {/* Right: score + CTA */}
        <div className="flex flex-col items-end gap-3 shrink-0">
          <div className="text-right">
            <p className="text-xs text-[#4B5563] mb-0.5">저평가 점수</p>
            <p
              className="text-4xl font-extrabold tabular-nums"
              style={{ color: scoreCol }}
            >
              {Math.round(enhanced(stock))}
              <span className="text-lg font-normal text-[#374151]">/100</span>
            </p>
          </div>
          <button
            onClick={() =>
              navigate(`/stock/${encodeURIComponent(stock.ticker)}`)
            }
            className="text-sm font-bold text-white bg-[#0066FF] px-4 py-2 rounded-xl hover:bg-[#0052CC] transition-colors"
          >
            분석 전체 보기 →
          </button>
        </div>
      </div>
    </div>
  );
}

function NewPicksSection({ stocks }: { stocks: Stock[] }) {
  const navigate = useNavigate();
  if (stocks.length === 0) return null;

  return (
    <section>
      <div className="flex items-center gap-2 mb-3">
        <Sparkles size={15} className="text-[#10B981]" />
        <span className="text-base font-bold text-[#191F28]">이번 주 신규 등장</span>
        <span className="text-xs font-bold text-white bg-[#10B981] px-2 py-0.5 rounded-full">
          {stocks.length}종목
        </span>
        <span className="text-xs text-[#8B95A1]">· 지난 분석 대비 새로 진입</span>
      </div>
      <div className="border border-[#A7F3D0] rounded-2xl overflow-hidden shadow-sm bg-[#F0FDF4]/40">
        <table className="w-full">
          <thead>
            <tr className="bg-[#ECFDF5] border-b border-[#A7F3D0]">
              <th className="px-3 sm:px-5 py-3 text-left text-xs font-medium text-[#B0B8C1]">#</th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1]">종목</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1]">현재가</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden sm:table-cell">P/E</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden sm:table-cell">P/B</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden md:table-cell">ROE</th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1]">점수</th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1] hidden lg:table-cell">저평가 근거</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((s, i) => (
              <tr
                key={s.ticker}
                onClick={() => navigate(`/stock/${encodeURIComponent(s.ticker)}`)}
                className="border-b border-[#D1FAE5] last:border-0 hover:bg-[#F0FDF4] cursor-pointer transition-colors"
              >
                <td className="px-3 sm:px-5 py-2.5 sm:py-3.5 text-sm text-[#B0B8C1] tabular-nums">{i + 1}</td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5">
                  <div className="flex flex-col">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-bold text-[#191F28] tracking-tight">{s.ticker}</span>
                      <span className="text-[9px] font-bold text-white bg-[#10B981] px-1 py-0.5 rounded">NEW</span>
                    </div>
                    <span className="text-xs text-[#8B95A1] mt-0.5 truncate max-w-25 sm:max-w-40">{s.name}</span>
                  </div>
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm font-medium text-[#191F28] tabular-nums">
                  {fmtPrice(s.data?.current_price, s.market)}
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm text-[#191F28] tabular-nums hidden sm:table-cell">
                  {fmt(s.data?.pe_ratio, 1, "x")}
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm text-[#191F28] tabular-nums hidden sm:table-cell">
                  {fmt(s.data?.pb_ratio, 2, "x")}
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right text-sm text-[#191F28] tabular-nums hidden md:table-cell">
                  {s.data?.roe != null ? fmt(s.data.roe * 100, 1, "%") : "—"}
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5">
                  <div className="flex items-center gap-1.5">
                    <ScoreBar score={enhanced(s)} />
                    {s.investment_tier && (
                      <span
                        className="text-[10px] font-bold text-white px-1.5 py-0.5 rounded shrink-0"
                        style={{
                          background: s.investment_tier === 1 ? '#D97706'
                            : s.investment_tier === 2 ? '#0066FF'
                            : '#6B7280',
                        }}
                      >
                        T{s.investment_tier}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs text-[#8B95A1] max-w-55 hidden lg:table-cell">
                  <span className="line-clamp-2">{s.reasoning}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function HomePage() {
  const market: Market = "nasdaq";
  const [sectors, setSectors] = useState<Record<string, Stock[]>>({});
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [topPick, setTopPick] = useState<Stock | null>(null);
  const [newPicks, setNewPicks] = useState<Stock[]>([]);

  const loadSectors = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getSectors("nasdaq");
      const filtered: Record<string, Stock[]> = {};
      for (const [sector, stocks] of Object.entries(data)) {
        const top = stocks.filter((s) => s.investment_tier != null);
        if (top.length > 0) filtered[sector] = top;
      }
      setSectors(filtered);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    api.getStatus().then(setStatus).catch(() => {});
    api.getTopPick("nasdaq").then(setTopPick).catch(() => setTopPick(null));
    api.getNewPicks().then(setNewPicks).catch(() => setNewPicks([]));
    loadSectors();
  }, [loadSectors]);

  const totalStocks = Object.values(sectors).reduce(
    (s, arr) => s + arr.length,
    0,
  );
  const currentSnapshot = status?.snapshots[market];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-white border-b border-[#E8EAED]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <Link
              to="/"
              className="flex items-center gap-3 hover:opacity-75 transition-opacity shrink-0"
            >
              <div className="w-7 h-7 rounded-lg bg-[#0066FF] flex items-center justify-center">
                <TrendingDown size={14} color="white" />
              </div>
              <span className="text-base font-bold text-[#191F28]">
                텐배거 레이더
              </span>
            </Link>

            {/* Right group */}
            <div className="flex items-center gap-2 sm:gap-3">
              {/* Page nav tabs */}
              <div className="flex items-center gap-1 bg-[#F2F4F6] rounded-xl p-1">
                <span className="px-2.5 sm:px-4 py-1.5 text-xs sm:text-sm font-semibold rounded-lg bg-white text-[#191F28] shadow-sm">
                  저평가 종목
                </span>
                <Link
                  to="/swing"
                  className="px-2.5 sm:px-4 py-1.5 text-xs sm:text-sm font-semibold rounded-lg text-[#8B95A1] hover:text-[#191F28] transition-all"
                >
                  스윙 후보
                </Link>
              </div>
              {/* Search + status — desktop only */}
              <div className="hidden sm:flex items-center gap-2">
                <TickerSearch />
                <LastUpdatedBadge
                  snapshot={currentSnapshot ?? null}
                />
              </div>
            </div>
          </div>
          {/* Mobile search row */}
          <div className="sm:hidden pb-2.5">
            <TickerSearch className="w-full" />
          </div>
        </div>
      </header>

      {/* Run log — 수집 이력 (관리자용, 비표시) */}

      {/* Sub-stats bar */}
      {status && (
        <div className="bg-[#F9FAFB] border-b border-[#E8EAED]">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[#8B95A1]">
            <span>
              나스닥{" "}
              <span className="text-[#191F28] font-semibold">
                {status.nasdaq_stocks}
              </span>
              종목
            </span>
            {totalStocks > 0 && (
              <span>
                <span className="text-[#0066FF] font-semibold">
                  {totalStocks}
                </span>
                종목 표시 중
                <span className="ml-1.5 text-[#B0B8C1]">· 심층분석 상위 10종목</span>
              </span>
            )}
            <span className="hidden sm:inline text-[#B0B8C1]">
              매주 월요일 07:10 자동 수집
            </span>
          </div>
        </div>
      )}

      {/* Main */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 gap-4">
            <div className="w-8 h-8 border-2 border-[#0066FF] border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-[#8B95A1]">데이터 로딩 중...</p>
          </div>
        ) : Object.keys(sectors).length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 gap-4 text-center">
            <div className="w-16 h-16 rounded-2xl bg-[#F2F4F6] flex items-center justify-center">
              <TrendingDown size={28} color="#B0B8C1" />
            </div>
            <div>
              <p className="text-base font-semibold text-[#191F28] mb-1">
                아직 분석 데이터가 없습니다
              </p>
              <p className="text-sm text-[#8B95A1]">
                터미널에서 아래 명령어를 실행해 첫 수집을 시작하세요
              </p>
            </div>
            <div className="bg-[#F2F4F6] rounded-xl px-6 py-4 text-left font-mono text-sm text-[#191F28]">
              <p className="text-[#8B95A1] text-xs mb-2">
                # backend 폴더에서 실행
              </p>
              <p>python collect.py --market nasdaq</p>
            </div>
            <p className="text-xs text-[#B0B8C1]">
              약 10~15분 소요 · 이후 매일 자동 실행됩니다
            </p>
          </div>
        ) : (
          <div className="space-y-10">
            {topPick && <TopPickCard stock={topPick} />}
            <NewPicksSection stocks={newPicks} />
            <Tier1Section sectors={sectors} />
            {Object.entries(sectors).map(([sector, stocks]) => (
              <SectorTable key={sector} sector={sector} stocks={stocks} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
