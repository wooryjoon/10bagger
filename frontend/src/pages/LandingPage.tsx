import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  TrendingUp,
  Shield,
  BarChart2,
  ArrowRight,
  CheckCircle,
  Zap,
  Globe,
  Activity,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Stock } from "@/types";

// ── 상단 네비게이션 ───────────────────────────────────────────────────────────
function Navbar() {
  const navigate = useNavigate();
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-[#E8EAED]">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#0066FF] flex items-center justify-center">
            <TrendingUp size={14} color="white" />
          </div>
          <span className="font-bold text-[#191F28] text-base">
            텐배거 레이더
          </span>
        </div>
        <button
          onClick={() => navigate("/app")}
          className="px-4 py-2 rounded-xl bg-[#0066FF] text-white text-sm font-semibold hover:bg-[#0052CC] transition-colors"
        >
          분석 결과 보기
        </button>
      </div>
    </nav>
  );
}

const CARD_COLORS = ["#0066FF", "#7C3AED", "#059669"];

function chartTag(stock: Stock): string {
  const bd = stock.score_breakdown ?? {};
  if ((bd.golden_cross?.score ?? 0) > 0) return "골든크로스";
  if ((bd.disparity_ratio?.score ?? 0) > 0) return "MA200 이격도";
  if ((bd.momentum_20d?.score ?? 0) > 0) return "20일 모멘텀";
  return "재무 우량";
}

// ── 히어로 ───────────────────────────────────────────────────────────────────
function Hero() {
  const navigate = useNavigate();
  const [top3, setTop3] = useState<Stock[]>([]);

  useEffect(() => {
    api.getStocks("nasdaq", 3).then(setTop3).catch(() => {});
  }, []);

  return (
    <section className="relative pt-32 pb-24 overflow-hidden bg-[#0A0F1C]">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full bg-[#0066FF]/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[300px] rounded-full bg-purple-600/10 blur-[100px] pointer-events-none" />

      <div className="relative max-w-6xl mx-auto px-6 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#0066FF]/10 border border-[#0066FF]/30 mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-[#60A5FA] animate-pulse" />
          <span className="text-[#93C5FD] text-xs font-semibold">
            NASDAQ 190종목 · 매일 자동 분석
          </span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-white leading-tight mb-6">
          오를 종목을
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#4D9FFF] to-[#A78BFA]">
            데이터로 찾습니다
          </span>
        </h1>

        <p className="text-[#8B95A1] text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed mb-10">
          재무 성장성, 차트 모멘텀, 현금흐름, 내부자 신호.
          <br className="hidden sm:block" />
          4단계 정량 분석으로 저평가 성장주를 매일 업데이트합니다.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => navigate("/app")}
            className="flex items-center gap-2 px-7 py-3.5 rounded-2xl bg-[#0066FF] text-white font-bold text-base hover:bg-[#0052CC] transition-all hover:scale-105 shadow-lg shadow-[#0066FF]/30"
          >
            오늘 분석 결과 보기
            <ArrowRight size={17} />
          </button>
          <span className="text-[#4B5563] text-sm">
            로그인 없음 · 광고 없음 · 무료
          </span>
        </div>

        <div className="mt-16 flex flex-wrap justify-center gap-3 max-w-2xl mx-auto">
          {top3.length > 0
            ? top3.map((stock, i) => {
                const color = CARD_COLORS[i] ?? "#0066FF";
                return (
                  <div
                    key={stock.ticker}
                    className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm"
                  >
                    <div className="text-left">
                      <p className="text-white font-bold text-sm">{stock.ticker}</p>
                      <p style={{ color }} className="text-xs font-medium">
                        {chartTag(stock)}
                      </p>
                    </div>
                    <div className="w-px h-8 bg-white/10" />
                    <div className="text-right">
                      <p className="text-xs text-[#8B95A1]">점수</p>
                      <p style={{ color }} className="text-lg font-extrabold tabular-nums">
                        {stock.score}
                      </p>
                    </div>
                  </div>
                );
              })
            : Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-white/5 border border-white/10 animate-pulse"
                >
                  <div className="text-left space-y-1">
                    <div className="w-12 h-3 rounded bg-white/10" />
                    <div className="w-16 h-2 rounded bg-white/10" />
                  </div>
                  <div className="w-px h-8 bg-white/10" />
                  <div className="text-right space-y-1">
                    <div className="w-6 h-2 rounded bg-white/10" />
                    <div className="w-8 h-5 rounded bg-white/10" />
                  </div>
                </div>
              ))}
        </div>
      </div>
    </section>
  );
}

// ── 지표 숫자 ─────────────────────────────────────────────────────────────────
function Stats() {
  const items = [
    { value: "190", label: "NASDAQ 분석 종목" },
    { value: "4", label: "정량 분석 단계" },
    { value: "12", label: "평가 세부 지표" },
    { value: "매일", label: "자동 업데이트" },
  ];
  return (
    <section className="py-14 border-b border-[#E8EAED] bg-white">
      <p className="text-center text-sm font-medium text-[#8B95A1] mb-8">
        재무·차트·현금흐름·내부자 신호를 동시에 분석해 최적 타이밍을 찾습니다
      </p>
      <div className="max-w-6xl mx-auto px-6 grid grid-cols-2 sm:grid-cols-4 gap-8 text-center">
        {items.map((s) => (
          <div key={s.label}>
            <p className="text-4xl font-extrabold text-[#0066FF] tabular-nums mb-1">
              {s.value}
            </p>
            <p className="text-sm text-[#8B95A1] font-medium">{s.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── 4단계 분석 모듈 ────────────────────────────────────────────────────────────
function HowItWorks() {
  const modules = [
    {
      icon: <Shield size={24} color="#0066FF" />,
      badge: "60점",
      badgeColor: "#EFF6FF",
      badgeText: "#0066FF",
      step: "01",
      title: "재무 스크리닝",
      subtitle: "성장하는 기업인가?",
      desc: "3년 매출 성장 궤적, Rule of 40, PSR 저평가를 동시에 검증합니다. 매출 성장과 수익성이 함께 개선되는 기업만 통과합니다.",
      items: [
        "매출 3년 성장률 — 실질 성장 궤적 확인",
        "Rule of 40 — 성장률 + 영업이익률 합산",
        "PSR — 주가매출비율 저평가 여부",
      ],
      bg: "from-[#EFF6FF] to-white",
      border: "border-[#BFDBFE]",
    },
    {
      icon: <Activity size={24} color="#059669" />,
      badge: "30점",
      badgeColor: "#ECFDF5",
      badgeText: "#059669",
      step: "02",
      title: "차트 모멘텀 분석",
      subtitle: "상승 추세인가?",
      desc: "골든크로스, MA200 이격도, 20일 모멘텀으로 추세 전환 시점을 포착합니다. 2년 백테스트 결과 골든크로스 신호 후 90일 평균 수익률 +9.8%.",
      items: [
        "골든크로스(MA20 > MA60) — 백테스트 검증 핵심 신호",
        "MA200 이격도 — 역사적 저점 대비 현재 위치",
        "20일 모멘텀 — 단기 가격 상승 탄력 확인",
      ],
      bg: "from-[#ECFDF5] to-white",
      border: "border-[#A7F3D0]",
    },
    {
      icon: <Zap size={24} color="#7C3AED" />,
      badge: "10점",
      badgeColor: "#F5F3FF",
      badgeText: "#7C3AED",
      step: "03",
      title: "현금흐름 검증",
      subtitle: "지속 가능한 사업인가?",
      desc: "R&D 투자, 설비투자 추세, EV/EBITDA로 사업의 내구성을 검증합니다. 성장 외형 뒤에 실질 수익 구조가 뒷받침되는지 확인합니다.",
      items: [
        "R&D 비율 — 미래 성장 투자 수준",
        "CapEx 3년 추세 — 설비투자 효율성",
        "EV/EBITDA — 기업 가치 대비 수익성",
      ],
      bg: "from-[#F5F3FF] to-white",
      border: "border-[#DDD6FE]",
    },
    {
      icon: <Globe size={24} color="#D97706" />,
      badge: "+15점",
      badgeColor: "#FFFBEB",
      badgeText: "#D97706",
      step: "04",
      title: "심층 분석",
      subtitle: "스마트머니 신호가 있는가?",
      desc: "경영진 내부자 매수, 기관 보유율 증가, 뉴스 감성 지표를 종합합니다. 재무와 차트가 좋은 종목 중 상위 10개에만 적용됩니다.",
      items: [
        "내부자 거래 — 경영진 매수 포지션",
        "기관 보유율 — 스마트머니 유입 추이",
        "뉴스 감성 — 비관론 극점 역발상 신호",
      ],
      bg: "from-[#FFFBEB] to-white",
      border: "border-[#FDE68A]",
    },
  ];

  return (
    <section className="py-24 bg-[#F9FAFB]">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <p className="text-sm font-bold text-[#0066FF] uppercase tracking-widest mb-3">
            How It Works
          </p>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#191F28] mb-4">
            4단계 정량 분석
          </h2>
          <p className="text-[#8B95A1] text-base max-w-xl mx-auto">
            재무 성장성부터 차트 모멘텀까지, 12개 지표로 저평가 종목을 선별합니다.
            <br />
            좋은 기업이 좋은 타이밍에 있을 때만 높은 점수가 나옵니다.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {modules.map((m) => (
            <div
              key={m.step}
              className={`rounded-3xl border bg-gradient-to-b ${m.bg} ${m.border} p-7 flex flex-col gap-5`}
            >
              <div className="flex items-center justify-between">
                <div
                  className="w-11 h-11 rounded-2xl flex items-center justify-center"
                  style={{ background: m.badgeColor }}
                >
                  {m.icon}
                </div>
                <span
                  className="text-xs font-bold px-2.5 py-1 rounded-full"
                  style={{ background: m.badgeColor, color: m.badgeText }}
                >
                  {m.badge}
                </span>
              </div>

              <div>
                <p className="text-xs font-semibold text-[#8B95A1] mb-1">
                  STAGE {m.step}
                </p>
                <h3 className="text-xl font-extrabold text-[#191F28] mb-1">
                  {m.title}
                </h3>
                <p className="text-sm font-semibold text-[#4B5563]">
                  {m.subtitle}
                </p>
              </div>

              <p className="text-sm text-[#6B7280] leading-relaxed">{m.desc}</p>

              <ul className="space-y-2">
                {m.items.map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-2 text-xs text-[#374151]"
                  >
                    <CheckCircle
                      size={13}
                      style={{ color: m.badgeText }}
                      className="shrink-0 mt-0.5"
                    />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 rounded-3xl bg-[#0A0F1C] p-8 text-center">
          <p className="text-[#8B95A1] text-sm mb-4">최종 점수 산출 공식</p>
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm sm:text-base font-bold">
            <span className="text-[#60A5FA]">재무 스크리닝 60점</span>
            <span className="text-white">+</span>
            <span className="text-[#34D399]">차트 모멘텀 30점</span>
            <span className="text-white">+</span>
            <span className="text-[#A78BFA]">현금흐름 10점</span>
            <span className="text-white">+</span>
            <span className="text-[#FCD34D]">심층분석 최대 +15점</span>
            <span className="text-white">=</span>
            <span className="text-white text-lg sm:text-xl">최대 115점</span>
          </div>
        </div>
      </div>
    </section>
  );
}

// ── 신뢰 포인트 ───────────────────────────────────────────────────────────────
function WhyUs() {
  const points = [
    {
      icon: <BarChart2 size={22} color="#0066FF" />,
      title: "12개 지표, 하나의 점수",
      desc: "PSR, Rule of 40, 골든크로스, EV/EBITDA 등 12개 정량 지표를 단일 점수로 통합합니다. 어떤 종목이 더 나은지 한눈에 비교할 수 있습니다.",
    },
    {
      icon: <Zap size={22} color="#7C3AED" />,
      title: "백테스트로 검증된 신호",
      desc: "NASDAQ 190종목, 최근 2년 데이터 기준 — 골든크로스 신호 후 90일 평균 수익률 +9.8%, 승률 54.8% (374건). 실적이 없는 신호는 채택하지 않습니다.",
    },
    {
      icon: <TrendingUp size={22} color="#059669" />,
      title: "재무와 차트의 교집합",
      desc: "재무가 탄탄한 기업이 차트 모멘텀까지 살아 있을 때만 높은 점수가 나옵니다. 좋은 기업을 좋은 타이밍에 찾는 것, 그게 이 분석의 핵심입니다.",
    },
  ];
  return (
    <section className="py-24 bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-14">
          <p className="text-sm font-bold text-[#0066FF] uppercase tracking-widest mb-3">
            Why Quant Pick
          </p>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#191F28]">
            왜 정량 분석인가요?
          </h2>
        </div>
        <div className="grid sm:grid-cols-3 gap-6">
          {points.map((p) => (
            <div
              key={p.title}
              className="p-7 rounded-3xl border border-[#E8EAED] hover:border-[#BFDBFE] hover:shadow-lg hover:shadow-blue-50 transition-all"
            >
              <div className="w-11 h-11 rounded-2xl bg-[#F9FAFB] flex items-center justify-center mb-5">
                {p.icon}
              </div>
              <h3 className="text-base font-extrabold text-[#191F28] mb-2">
                {p.title}
              </h3>
              <p className="text-sm text-[#6B7280] leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── 최하단 CTA ────────────────────────────────────────────────────────────────
function CTA() {
  const navigate = useNavigate();
  return (
    <section className="py-24 bg-[#0A0F1C] relative overflow-hidden">
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[600px] h-[300px] rounded-full bg-[#0066FF]/15 blur-[100px]" />
      </div>
      <div className="relative max-w-2xl mx-auto px-6 text-center">
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
          오늘의 분석 결과를 확인하세요
        </h2>
        <p className="text-[#8B95A1] text-base mb-10">
          NASDAQ 190종목 분석 결과가 매일 업데이트됩니다.
          <br />
          로그인 없이 바로 확인할 수 있습니다.
        </p>
        <button
          onClick={() => navigate("/app")}
          className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-[#0066FF] text-white font-bold text-base hover:bg-[#0052CC] transition-all hover:scale-105 shadow-xl shadow-[#0066FF]/30"
        >
          분석 결과 보기
          <ArrowRight size={18} />
        </button>
        <p className="mt-4 text-[#4B5563] text-sm">
          무료 · 회원가입 없음 · 광고 없음
        </p>
      </div>
    </section>
  );
}

// ── 푸터 ─────────────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer className="py-8 border-t border-[#1F2937] bg-[#0A0F1C]">
      <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-md bg-[#0066FF] flex items-center justify-center">
            <TrendingUp size={10} color="white" />
          </div>
          <span className="text-[#4B5563] text-sm font-semibold">
            Quant Pick
          </span>
        </div>
        <p className="text-[#374151] text-xs text-center">
          본 서비스는 투자 정보 제공 목적이며, 투자 권유가 아닙니다. 투자 결정은
          본인의 책임입니다.
        </p>
      </div>
    </footer>
  );
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <Hero />
      <Stats />
      <HowItWorks />
      <WhyUs />
      <CTA />
      <Footer />
    </div>
  );
}
