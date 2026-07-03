import { useState, useEffect, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { TrendingUp, AlertCircle, Search } from "lucide-react";
import { api } from "@/lib/api";
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
    : "$" + val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? "#0066FF" : score >= 50 ? "#6B8FE8" : "#B0B8C1";
  return (
    <div className="flex items-center gap-2">
      <div className="w-14 h-1.5 rounded-full bg-[#F2F4F6] overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="text-sm font-bold tabular-nums" style={{ color }}>
        {Math.round(score)}
      </span>
    </div>
  );
}

function SwingBadge({ score }: { score: number }) {
  const color = score >= 8 ? "#059669" : score >= 6 ? "#D97706" : "#6B7280";
  return (
    <span
      className="text-[10px] font-bold px-1.5 py-0.5 rounded border shrink-0"
      style={{ color, borderColor: color, background: `${color}15` }}
    >
      스윙 {score}/10
    </span>
  );
}

function StockRow({ rank, stock }: { rank: number; stock: Stock }) {
  const navigate = useNavigate();
  const m = stock.data;
  const swingText = stock.swing_reasoning || "—";

  return (
    <tr
      onClick={() => navigate(`/stock/${encodeURIComponent(stock.ticker)}`)}
      className="border-b border-[#F2F4F6] last:border-0 hover:bg-[#F9FAFB] cursor-pointer transition-colors"
    >
      <td className="px-3 sm:px-5 py-2.5 sm:py-3.5 text-sm text-[#B0B8C1] tabular-nums">{rank}</td>
      <td className="px-2 sm:px-4 py-2.5 sm:py-3.5">
        <div className="flex flex-col">
          <span className="text-sm font-bold text-[#191F28] tracking-tight">{stock.ticker}</span>
          <span className="text-xs text-[#8B95A1] mt-0.5 truncate max-w-25 sm:max-w-40">{stock.name}</span>
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
        <div className="flex flex-col gap-1">
          <ScoreBar score={stock.score} />
          {stock.swing_score != null && <SwingBadge score={stock.swing_score} />}
        </div>
      </td>
      <td className="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs text-[#8B95A1] max-w-55 hidden lg:table-cell">
        <span className="line-clamp-2">{swingText}</span>
      </td>
    </tr>
  );
}

function SectorTable({ sector, stocks }: { sector: string; stocks: Stock[] }) {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-base font-bold text-[#191F28]">{SECTOR_KO[sector] ?? sector}</span>
          <span className="text-xs text-[#8B95A1] bg-[#F2F4F6] px-2 py-0.5 rounded-full">{sector}</span>
        </div>
        <span className="text-xs text-[#B0B8C1]">{stocks.length}종목</span>
      </div>
      <div className="border border-[#E8EAED] rounded-2xl overflow-hidden shadow-sm">
        <table className="w-full">
          <thead>
            <tr className="bg-[#F9FAFB] border-b border-[#E8EAED]">
              <th className="px-3 sm:px-5 py-3 text-left text-xs font-medium text-[#B0B8C1]">#</th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1]">종목</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1]">현재가</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden sm:table-cell">P/E</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden sm:table-cell">P/B</th>
              <th className="px-2 sm:px-4 py-3 text-right text-xs font-medium text-[#B0B8C1] hidden md:table-cell">ROE</th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1]">점수</th>
              <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-[#B0B8C1] hidden lg:table-cell">스윙 신호</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((s, i) => <StockRow key={s.ticker} rank={i + 1} stock={s} />)}
          </tbody>
        </table>
      </div>
    </section>
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
    <div className={`flex items-center gap-1 bg-[#F2F4F6] rounded-xl px-3 py-1.5 ${className ?? ""}`}>
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
        <button onClick={submit} className="text-[11px] font-bold text-white bg-[#0066FF] px-2 py-0.5 rounded-lg shrink-0">
          분석
        </button>
      )}
    </div>
  );
}

export default function SwingPage() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getSwing();
      setStocks(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Group by sector, sorted by swing_score within each sector
  const sectors: Record<string, Stock[]> = {};
  for (const s of stocks) {
    const sec = s.sector || "Unknown";
    if (!sectors[sec]) sectors[sec] = [];
    sectors[sec].push(s);
  }
  for (const arr of Object.values(sectors)) {
    arr.sort((a, b) => (b.swing_score ?? 0) - (a.swing_score ?? 0));
  }

  const totalStocks = stocks.length;

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-white border-b border-[#E8EAED]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            <Link to="/" className="flex items-center gap-3 hover:opacity-75 transition-opacity shrink-0">
              <div className="w-7 h-7 rounded-lg bg-[#059669] flex items-center justify-center">
                <TrendingUp size={14} color="white" />
              </div>
              <span className="text-base font-bold text-[#191F28]">스윙 후보</span>
            </Link>

            <div className="flex items-center gap-2 sm:gap-3">
              {/* Page nav tabs */}
              <div className="flex items-center gap-1 bg-[#F2F4F6] rounded-xl p-1">
                <Link
                  to="/app"
                  className="px-2.5 sm:px-4 py-1.5 text-xs sm:text-sm font-semibold rounded-lg text-[#8B95A1] hover:text-[#191F28] transition-all"
                >
                  저평가 종목
                </Link>
                <span className="px-2.5 sm:px-4 py-1.5 text-xs sm:text-sm font-semibold rounded-lg bg-white text-[#191F28] shadow-sm">
                  스윙 후보
                </span>
              </div>
              <div className="hidden sm:flex items-center gap-2">
                <TickerSearch />
              </div>
            </div>
          </div>
          <div className="sm:hidden pb-2.5">
            <TickerSearch className="w-full" />
          </div>
        </div>
      </header>

      {/* Sub-stats bar */}
      <div className="bg-[#F9FAFB] border-b border-[#E8EAED]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[#8B95A1]">
          <span>
            스윙 후보{" "}
            <span className="text-[#191F28] font-semibold">{totalStocks}</span>종목
          </span>
          <span className="text-[#B0B8C1]">· 스윙점수 5/10 이상 · NASDAQ</span>
          <span className="hidden sm:inline text-[#B0B8C1]">· 5개 기술적 신호 기반 · 10% 수익 목표</span>
        </div>
      </div>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 gap-4">
            <div className="w-8 h-8 border-2 border-[#059669] border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-[#8B95A1]">스윙 후보 분석 중...</p>
          </div>
        ) : stocks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 gap-4 text-center">
            <div className="w-16 h-16 rounded-2xl bg-[#F2F4F6] flex items-center justify-center">
              <AlertCircle size={28} color="#B0B8C1" />
            </div>
            <div>
              <p className="text-base font-semibold text-[#191F28] mb-1">스윙 후보 데이터가 없습니다</p>
              <p className="text-sm text-[#8B95A1]">다음 수집 후 자동으로 표시됩니다 (매일 07:10)</p>
            </div>
          </div>
        ) : (
          <div className="space-y-10">
            {Object.entries(sectors)
              .sort(([, a], [, b]) => (b[0]?.swing_score ?? 0) - (a[0]?.swing_score ?? 0))
              .map(([sector, sectorStocks]) => (
                <SectorTable key={sector} sector={sector} stocks={sectorStocks} />
              ))}
          </div>
        )}
      </main>
    </div>
  );
}
