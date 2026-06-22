"""
Quant Screening — Undervalued Growth Stocks
Total Score = Financial(60) + Chart(30) + CashFlow(10) = 100

Target: High-growth companies investing in R&D/CapEx → low/negative OPM,
        currently at chart oversold bottom (RSI ≤ 30, far below MA, volume dry-up).
"""
from __future__ import annotations
import math


# ── Stage 1: Financial Scoring (max 60) ──────────────────────────────────────

def score_financial(fd: dict) -> tuple[float, dict, list[str]]:
    """
    Scores growth + valuation. Penalises mature profitable companies (OPM > 20%).
    fd keys: rev_growth, revenue_cagr, operating_margin, price_to_sales,
             sector_avg_psr, pe_ratio, earnings_growth
    """
    reasons: list[str] = []

    opm      = fd.get("operating_margin")
    psr      = fd.get("price_to_sales")
    sect_psr = fd.get("sector_avg_psr")
    pe       = fd.get("pe_ratio")
    eg       = fd.get("earnings_growth")

    # Prefer multi-year CAGR; flag if falling back to single-year YoY
    using_cagr = fd.get("revenue_cagr") is not None
    growth     = fd.get("revenue_cagr") if using_cagr else fd.get("rev_growth")

    g_pct  = (growth or 0) * 100
    op_pct = (opm    or 0) * 100
    rule40 = g_pct + op_pct

    # ── Revenue Growth (0-25) ─────────────────────────────────────────────────
    if growth is None:
        gs = 3
    elif growth >= 0.50:
        gs = 25; reasons.append(f"매출 성장률 {g_pct:.0f}% — 폭발적 성장")
    elif growth >= 0.40:
        gs = 22; reasons.append(f"매출 성장률 {g_pct:.0f}%")
    elif growth >= 0.30:
        gs = 18; reasons.append(f"매출 성장률 {g_pct:.0f}%")
    elif growth >= 0.20:
        gs = 12; reasons.append(f"매출 성장률 {g_pct:.0f}%")
    elif growth >= 0.10:
        gs = 5
    else:
        gs = 0

    # ── Rule of 40 (0-20) ─────────────────────────────────────────────────────
    if growth is None:
        r40s = 3
    elif rule40 >= 60:
        r40s = 20; reasons.append(f"Rule of 40 = {rule40:.0f}% — 최우수")
    elif rule40 >= 50:
        r40s = 16; reasons.append(f"Rule of 40 = {rule40:.0f}%")
    elif rule40 >= 40:
        r40s = 10
    elif rule40 >= 30:
        r40s = 5
    elif rule40 >= 20:
        r40s = 2
    else:
        r40s = 0

    # ── PSR Valuation (0-15) ──────────────────────────────────────────────────
    ps = 5  # neutral default
    if psr is not None and psr > 0:
        if sect_psr and sect_psr > 0:
            ratio = psr / sect_psr
            if ratio <= 0.30:
                ps = 15; reasons.append(f"PSR {psr:.1f}x — 섹터 평균({sect_psr:.1f}x) 대비 극단 저평가")
            elif ratio <= 0.50:
                ps = 12; reasons.append(f"PSR {psr:.1f}x — 섹터 대비 저평가")
            elif ratio <= 0.70:
                ps = 8
            elif ratio <= 1.00:
                ps = 4
            else:
                ps = 0
        else:
            # Absolute PSR thresholds (no sector avg available)
            if psr <= 3:
                ps = 15; reasons.append(f"PSR {psr:.1f}x — 절대적 저평가")
            elif psr <= 6:
                ps = 10; reasons.append(f"PSR {psr:.1f}x")
            elif psr <= 10:
                ps = 6
            elif psr <= 15:
                ps = 3
            else:
                ps = 0

        # PEG bonus for profitable companies
        if pe and eg and eg > 0.01 and pe > 0:
            peg = pe / (eg * 100)
            if peg <= 0.5:
                ps = min(15, ps + 4); reasons.append(f"PEG {peg:.2f} — 성장 대비 저평가")
            elif peg <= 1.0:
                ps = min(15, ps + 2)

    # YoY는 단년도 스냅샷 — CAGR 대비 신뢰도 낮으므로 20% 할인
    if not using_cagr and growth is not None:
        gs    = round(gs    * 0.8, 1)
        r40s  = round(r40s  * 0.8, 1)

    # ── OPM Gate: penalise mature profitable companies ────────────────────────
    # OPM > 20% = not a "heavily-investing growth" company → cap at 25% of max
    if opm is not None and opm > 0.20:
        raw   = gs + r40s + ps
        total = min(15, round(raw * 0.25, 1))
        bd = {
            "revenue_growth": {"score": round(gs * 0.25, 1),   "max": 25, "value": round(g_pct, 1) if growth is not None else None},
            "rule_of_40":     {"score": round(r40s * 0.25, 1), "max": 20, "value": round(rule40, 1)},
            "psr_valuation":  {"score": round(ps * 0.25, 1),   "max": 15, "value": round(psr, 2) if psr is not None else None},
        }
        return total, bd, [f"영업이익률 {op_pct:.0f}% — 성숙 수익 기업 (투자 성장주 스크린 대상 아님)"]

    total = min(60, max(0.0, round(gs + r40s + ps, 1)))
    bd = {
        "revenue_growth": {"score": round(gs, 1),   "max": 25, "value": round(g_pct, 1) if growth is not None else None},
        "rule_of_40":     {"score": round(r40s, 1), "max": 20, "value": round(rule40, 1)},
        "psr_valuation":  {"score": round(ps, 1),   "max": 15, "value": round(psr, 2) if psr is not None else None},
    }
    return total, bd, reasons


# ── Stage 2: Chart Scoring (max 30) ──────────────────────────────────────────

def score_chart(history: list[dict]) -> tuple[float, dict, list[str]]:
    """
    Contrarian bottom signals: RSI oversold + far below long-term MA + volume dry-up.
    history: list of {"date","open","high","low","close","volume"}
    """
    reasons: list[str] = []
    empty_bd = {
        "rsi_oversold":    {"score": 0, "max": 10, "value": None},
        "disparity_ratio": {"score": 0, "max": 10, "value": None},
        "volume_dryup":    {"score": 0, "max": 10, "value": None},
    }

    if not history or len(history) < 30:
        return 0.0, empty_bd, ["차트 데이터 부족 (30일 미만)"]

    closes        = [d["close"]  for d in history]
    volumes       = [d["volume"] for d in history]
    current_price = closes[-1]

    # ── 1. RSI(14) Oversold — current or recently touched 30 (0-10) ──────────
    rsi_series: list[float] = []
    for i in range(10, 0, -1):
        sub = closes[:-i]
        if len(sub) >= 15:
            rsi_series.append(_rsi(sub))
    rsi_series.append(_rsi(closes))

    current_rsi = rsi_series[-1]
    min_10d     = min(rsi_series) if rsi_series else 50.0
    recovering  = (len(rsi_series) >= 4
                   and min_10d <= 32
                   and rsi_series[-1] > rsi_series[-3])

    if current_rsi <= 25:
        rsi_score = 10; reasons.append(f"RSI {current_rsi:.0f} — 극단 과매도")
    elif current_rsi <= 30:
        rsi_score = 10; reasons.append(f"RSI {current_rsi:.0f} — 과매도 진입")
    elif recovering:
        rsi_score = 8;  reasons.append(f"RSI 과매도 후 반등 중 (최저 {min_10d:.0f})")
    elif current_rsi <= 40:
        rsi_score = 4
    elif current_rsi <= 45:
        rsi_score = 1
    else:
        rsi_score = 0

    # ── 2. Long-term Disparity — price vs MA120/200 ≤ 85% (0-10) ────────────
    disparity_score = 0
    disparity_val   = None
    ref_label       = ""

    if len(closes) >= 200:
        ma            = sum(closes[-200:]) / 200
        disparity_val = current_price / ma * 100
        ref_label     = "MA200"
    elif len(closes) >= 120:
        ma            = sum(closes[-120:]) / 120
        disparity_val = current_price / ma * 100
        ref_label     = "MA120"

    if disparity_val is not None:
        if disparity_val <= 75:
            disparity_score = 10; reasons.append(f"{ref_label} 이격도 {disparity_val:.0f}% — 극단 낙폭 과대")
        elif disparity_val <= 80:
            disparity_score = 10; reasons.append(f"{ref_label} 이격도 {disparity_val:.0f}% — 낙폭 과대")
        elif disparity_val <= 85:
            disparity_score = 7;  reasons.append(f"{ref_label} 이격도 {disparity_val:.0f}%")
        elif disparity_val <= 90:
            disparity_score = 3
        else:
            disparity_score = 0

    # ── 3. Volume Dry-up: volume ≤ 50% avg + near 6M low (0-10) ─────────────
    vol_score = 0
    vol_ratio = None

    if len(volumes) >= 25:
        # 3-day average to filter out single-day noise
        recent_vol  = sum(volumes[-3:]) / 3
        avg20_vol   = sum(volumes[-23:-3]) / 20
        if avg20_vol > 0:
            vol_ratio = recent_vol / avg20_vol * 100

            prices_6m   = closes[-min(126, len(closes)):]
            near_bottom = current_price <= min(prices_6m) * 1.05

            if vol_ratio <= 50 and near_bottom:
                vol_score = 10; reasons.append(f"거래량 고갈 {vol_ratio:.0f}% — 매도 소진 바닥권")
            elif vol_ratio <= 50:
                vol_score = 5
            elif near_bottom and vol_ratio <= 70:
                vol_score = 4

    total = min(30, rsi_score + disparity_score + vol_score)
    bd = {
        "rsi_oversold":    {"score": round(rsi_score, 1),       "max": 10, "value": round(current_rsi, 1)},
        "disparity_ratio": {"score": round(disparity_score, 1), "max": 10, "value": round(disparity_val, 1) if disparity_val is not None else None},
        "volume_dryup":    {"score": round(vol_score, 1),       "max": 10, "value": round(vol_ratio, 1) if vol_ratio is not None else None},
    }
    return round(total, 1), bd, reasons


# ── Stage 3: Cash Flow Verification (max 10) ─────────────────────────────────

def score_cashflow(fd: dict) -> tuple[float, dict, list[str]]:
    """
    Validates healthy investment expenditure (R&D, CapEx, EV/EBITDA).
    fd keys: rd_ratio, capex_3y, ev_ebitda
    """
    reasons: list[str] = []

    rd    = fd.get("rd_ratio")
    capex = fd.get("capex_3y", [])
    ev_eb = fd.get("ev_ebitda")

    # R&D ratio (0-5)
    if rd is None:
        rd_score = 2
    elif rd >= 0.25:
        rd_score = 5; reasons.append(f"R&D {rd:.0%} — 강력한 기술 해자")
    elif rd >= 0.15:
        rd_score = 4; reasons.append(f"R&D {rd:.0%}")
    elif rd >= 0.10:
        rd_score = 2
    elif rd >= 0.05:
        rd_score = 1
    else:
        rd_score = 0

    # CapEx consistency (0-3)
    active = [v for v in capex if v is not None and v > 0]
    if len(active) >= 3:
        capex_score = 3; reasons.append("CapEx 3년 연속 투자")
    elif len(active) >= 2:
        capex_score = 2
    elif len(active) >= 1:
        capex_score = 1
    else:
        capex_score = 1  # unknown = neutral

    # EV/EBITDA (0-2)
    if ev_eb is None or ev_eb <= 0:
        ev_score = 1
    elif ev_eb < 15:
        ev_score = 2; reasons.append(f"EV/EBITDA {ev_eb:.0f}x — 매력적")
    elif ev_eb < 25:
        ev_score = 1
    else:
        ev_score = 0

    total = min(10, rd_score + capex_score + ev_score)
    bd = {
        "rd_ratio":          {"score": round(rd_score, 1),    "max": 5, "value": round(rd * 100, 1) if rd is not None else None},
        "capex_consistency": {"score": round(capex_score, 1), "max": 3, "value": None},
        "ev_ebitda_score":   {"score": round(ev_score, 1),    "max": 2, "value": round(ev_eb, 1) if ev_eb is not None and ev_eb > 0 else None},
    }
    return round(total, 1), bd, reasons


# ── Final Score ───────────────────────────────────────────────────────────────

def calculate_score(
    metrics: dict,
    sector_averages: dict | None = None,
    financial_data: dict | None = None,
    history: list[dict] | None = None,
    benchmark: list[dict] | None = None,  # unused, kept for backward compat
) -> tuple[float, dict, str]:
    """
    Total = Financial(max 60) + Chart(max 30) + CashFlow(max 10)
    """
    fd = {
        **(financial_data or {}),
        "operating_margin": metrics.get("operating_margin"),
        "price_to_sales":   metrics.get("price_to_sales"),
        "ev_ebitda":        metrics.get("ev_ebitda"),
        "rev_growth":       metrics.get("revenue_growth"),
        "pe_ratio":         metrics.get("pe_ratio"),
        "earnings_growth":  metrics.get("earnings_growth"),
        "sector_avg_psr":   (sector_averages or {}).get(metrics.get("sector", ""), None),
    }

    hist = history or []

    f_score,  f_bd,  f_reasons  = score_financial(fd)
    c_score,  c_bd,  c_reasons  = score_chart(hist)
    cf_score, cf_bd, cf_reasons = score_cashflow(fd)

    total = round(min(100.0, f_score + c_score + cf_score), 1)
    bd    = {**f_bd, **c_bd, **cf_bd}

    all_reasons = f_reasons + c_reasons + cf_reasons
    reasoning   = " · ".join(all_reasons[:6]) if all_reasons else "퀀트 분석 완료"
    return total, bd, reasoning


def compute_sector_averages(stocks: list[dict]) -> dict:
    """Stub — kept for backward compatibility."""
    return {}


# ── Utilities ─────────────────────────────────────────────────────────────────

def _rsi(closes: list[float], period: int = 14) -> float:
    """Wilder's RSI(14) — standard exponential smoothing, matches trading platforms."""
    if len(closes) < period + 2:
        return 50.0
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    # Seed: simple average of first `period` changes
    avg_gain = sum(d for d in deltas[:period] if d > 0) / period
    avg_loss = sum(-d for d in deltas[:period] if d < 0) / period
    # Wilder's smoothing over the rest
    for d in deltas[period:]:
        avg_gain = (avg_gain * (period - 1) + (d if d > 0 else 0)) / period
        avg_loss = (avg_loss * (period - 1) + (-d if d < 0 else 0)) / period
    if avg_loss == 0:
        return 100.0
    return round(100 - 100 / (1 + avg_gain / avg_loss), 1)


def _std(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    avg = sum(vals) / len(vals)
    return math.sqrt(sum((v - avg) ** 2 for v in vals) / len(vals))
