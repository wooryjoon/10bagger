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
            저평가 레이더
          </span>
        </div>
        <button
          onClick={() => navigate("/app")}
          className="px-4 py-2 rounded-xl bg-[#0066FF] text-white text-sm font-semibold hover:bg-[#0052CC] transition-colors"
        >
          분석 시작하기
        </button>
      </div>
    </nav>
  );
}

// ── 히어로 ───────────────────────────────────────────────────────────────────
function Hero() {
  const navigate = useNavigate();
  return (
    <section className="relative pt-32 pb-24 overflow-hidden bg-[#0A0F1C]">
      {/* 배경 글로우 */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full bg-[#0066FF]/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[300px] rounded-full bg-purple-600/10 blur-[100px] pointer-events-none" />

      <div className="relative max-w-6xl mx-auto px-6 text-center">
        {/* 배지 */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#0066FF]/10 border border-[#0066FF]/20 mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-[#0066FF] animate-pulse" />
          <span className="text-[#6B9FFF] text-xs font-semibold">
            NASDAQ 200종목 · 매일 자동 분석
          </span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-white leading-tight mb-6">
          다음 급등주를
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#4D9FFF] to-[#A78BFA]">
            AI가 먼저 찾아냅니다
          </span>
        </h1>

        <p className="text-[#8B95A1] text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed mb-10">
          재무 건전성 · 시장 테마 · 차트 타점을 결합한
          <br className="hidden sm:block" />
          3단계 하이브리드 스크리닝으로 저평가 종목을 발굴합니다
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => navigate("/app")}
            className="flex items-center gap-2 px-7 py-3.5 rounded-2xl bg-[#0066FF] text-white font-bold text-base hover:bg-[#0052CC] transition-all hover:scale-105 shadow-lg shadow-[#0066FF]/30"
          >
            무료로 분석 보기
            <ArrowRight size={17} />
          </button>
          <span className="text-[#4B5563] text-sm">로그인 없이 바로 확인</span>
        </div>

        {/* 미니 점수 프리뷰 카드 */}
        <div className="mt-16 flex flex-wrap justify-center gap-3 max-w-2xl mx-auto">
          {[
            { ticker: "NVDA", score: 81, tag: "AI 인프라", color: "#0066FF" },
            { ticker: "ADBE", score: 75, tag: "SaaS 저평가", color: "#7C3AED" },
            { ticker: "MU", score: 71, tag: "Memory 수요", color: "#059669" },
          ].map((s) => (
            <div
              key={s.ticker}
              className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm"
            >
              <div className="text-left">
                <p className="text-white font-bold text-sm">{s.ticker}</p>
                <p style={{ color: s.color }} className="text-xs font-medium">
                  {s.tag}
                </p>
              </div>
              <div className="w-px h-8 bg-white/10" />
              <div className="text-right">
                <p className="text-xs text-[#8B95A1]">점수</p>
                <p
                  style={{ color: s.color }}
                  className="text-lg font-extrabold tabular-nums"
                >
                  {s.score}
                </p>
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
    { value: "200", label: "NASDAQ 분석 종목" },
    { value: "3", label: "복합 분석 모듈" },
    { value: "9", label: "평가 세부 지표" },
    { value: "매일", label: "자동 업데이트" },
  ];
  return (
    <section className="py-14 border-b border-[#E8EAED] bg-white">
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

// ── 3단계 분석 모듈 ────────────────────────────────────────────────────────────
function HowItWorks() {
  const modules = [
    {
      icon: <Shield size={24} color="#0066FF" />,
      badge: "50%",
      badgeColor: "#EFF6FF",
      badgeText: "#0066FF",
      step: "01",
      title: "재무 건전성",
      subtitle: "진짜 돈을 버는 기업인가?",
      desc: "회계 장부가 아닌 실제 현금흐름을 봅니다. 적자 이력이 있거나 현금보다 부채가 많은 기업은 바로 탈락.",
      items: [
        "FCF 수익률 — 시가총액 대비 잉여현금",
        "순현금 비율 — 부채 없는 재무 방어선",
        "발생액 품질 — 이익의 진짜 현금화 여부",
      ],
      bg: "from-[#EFF6FF] to-white",
      border: "border-[#BFDBFE]",
    },
    {
      icon: <Globe size={24} color="#7C3AED" />,
      badge: "30%",
      badgeColor: "#F5F3FF",
      badgeText: "#7C3AED",
      step: "02",
      title: "시장 테마",
      subtitle: "지금 시장이 주목하는 산업인가?",
      desc: "AI가 현재 글로벌 시장의 핵심 테마를 추출하고, 그 테마에 속한 기업에 높은 점수를 부여합니다.",
      items: [
        "AI · 반도체 병목 현상",
        "전력 인프라 · 데이터센터 수요",
        "애널리스트 목표주가 업사이드",
      ],
      bg: "from-[#F5F3FF] to-white",
      border: "border-[#DDD6FE]",
    },
    {
      icon: <Activity size={24} color="#059669" />,
      badge: "20%",
      badgeColor: "#ECFDF5",
      badgeText: "#059669",
      step: "03",
      title: "차트 타점",
      subtitle: "지금이 사기 좋은 시점인가?",
      desc: "에너지가 응축된 타이밍을 포착합니다. 이평선이 모이고 거래량이 폭발하는 순간이 진입 신호입니다.",
      items: [
        "이평선 수렴 — 20/60/120일선 압축도",
        "거래량 폭발 — 60일 평균 대비 400%↑ 양봉",
        "상대 강도 — NASDAQ 지수 대비 초과 수익률",
      ],
      bg: "from-[#ECFDF5] to-white",
      border: "border-[#A7F3D0]",
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
            3가지 렌즈로 종목을 봅니다
          </h2>
          <p className="text-[#8B95A1] text-base max-w-xl mx-auto">
            좋은 기업이라도 타이밍이 맞지 않으면 수익이 없습니다.
            <br />
            재무·테마·차트를 동시에 분석해 최적 타점을 찾습니다.
          </p>
        </div>

        <div className="grid sm:grid-cols-3 gap-6">
          {modules.map((m) => (
            <div
              key={m.step}
              className={`rounded-3xl border bg-gradient-to-b ${m.bg} ${m.border} p-7 flex flex-col gap-5`}
            >
              {/* 헤더 */}
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
                  가중치 {m.badge}
                </span>
              </div>

              {/* 타이틀 */}
              <div>
                <p className="text-xs font-semibold text-[#8B95A1] mb-1">
                  MODULE {m.step}
                </p>
                <h3 className="text-xl font-extrabold text-[#191F28] mb-1">
                  {m.title}
                </h3>
                <p className="text-sm font-semibold text-[#4B5563]">
                  {m.subtitle}
                </p>
              </div>

              {/* 설명 */}
              <p className="text-sm text-[#6B7280] leading-relaxed">{m.desc}</p>

              {/* 체크리스트 */}
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

        {/* 최종 점수 공식 */}
        <div className="mt-10 rounded-3xl bg-[#0A0F1C] p-8 text-center">
          <p className="text-[#8B95A1] text-sm mb-4">최종 점수 산출 공식</p>
          <div className="flex flex-wrap items-center justify-center gap-3 text-base sm:text-lg font-bold">
            <span className="text-[#60A5FA]">재무 건전성 × 50%</span>
            <span className="text-white">+</span>
            <span className="text-[#A78BFA]">시장 테마 × 30%</span>
            <span className="text-white">+</span>
            <span className="text-[#34D399]">차트 타점 × 20%</span>
            <span className="text-white">=</span>
            <span className="text-white text-xl">최종 점수 (100점)</span>
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
      title: "감이 아닌 숫자",
      desc: "모든 판단은 공개된 재무제표와 시장 데이터를 기반으로 합니다. 주관적 의견 없이 오직 수치로만 평가합니다.",
    },
    {
      icon: <Zap size={22} color="#7C3AED" />,
      title: "AI가 테마를 분석",
      desc: "시시각각 변하는 시장 테마를 Claude AI가 읽고 어떤 산업이 주목받는지 자동으로 추출합니다.",
    },
    {
      icon: <TrendingUp size={22} color="#059669" />,
      title: "6개월 급등 가능성 타겟",
      desc: "단기 투기가 아닌 향후 6개월 내 실질적 상승 가능성에 초점을 맞춰 종목을 선별합니다.",
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
            왜 다른가요?
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
          오늘의 저평가 종목,
          <br />
          지금 바로 확인하세요
        </h2>
        <p className="text-[#8B95A1] text-base mb-10">
          NASDAQ 200종목 중 점수 상위 종목이 매일 업데이트됩니다.
        </p>
        <button
          onClick={() => navigate("/app")}
          className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-[#0066FF] text-white font-bold text-base hover:bg-[#0052CC] transition-all hover:scale-105 shadow-xl shadow-[#0066FF]/30"
        >
          무료로 분석 보기
          <ArrowRight size={18} />
        </button>
        <p className="mt-4 text-[#4B5563] text-sm">
          로그인 없이 · 광고 없이 · 무료
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
