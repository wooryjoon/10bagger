"""
Hybrid Quant Screening System
Final Score = Fundamental (50%) + Narrative (30%) + Technical (20%)
"""

from __future__ import annotations

import math


# ── Module 1: Fundamental Score (0-100) ──────────────────────────────────────

def score_fundamental(fd: dict) -> tuple[float, dict, list[str]]:
    """
    fd keys:
      op_income_3y, op_cf_3y, net_income_3y, fcf_yields_3y, current_fcf_yield,
      accruals_ok,
      current_ratio    (from metrics),
      rev_growth       (from metrics),
      ar_growth        (from balance sheet),
      inv_growth       (from balance sheet),
      dividend_yield   (from metrics),
      buyback_yield    (from cashflow),

    Returns (score 0-100 capped, breakdown, reasons).
    Max raw sum = 20+40+20+20+10+10 = 120 → capped at 100.
    """
    reasons: list[str] = []

    # ── Safety gate: 2+ yr consecutive Operating Income > 0 AND Op CF > 0 ──
    oi = fd.get("op_income_3y", [])
    ocf = fd.get("op_cf_3y", [])
    safety = (
        len(oi) >= 2 and all(v > 0 for v in oi[:2]) and
        len(ocf) >= 2 and all(v > 0 for v in ocf[:2])
    )
    safety_score = 20 if safety else 0

    if not safety:
        empty_bd = {
            "safety":           {"score": 0, "max": 20, "value": None},
            "fcf_yield":        {"score": 0, "max": 40, "value": None},
            "liquidity":        {"score": 0, "max": 20, "value": None},
            "accruals":         {"score": 0, "max": 20, "value": None},
            "quality_growth":   {"score": 0, "max": 10, "value": None},
            "shareholder_yield":{"score": 0, "max": 10, "value": None},
        }
        return 0.0, empty_bd, ["안전장치 미통과 — 영업이익·영업CF 연속 흑자 조건 불충족"]

    reasons.append("영업이익·영업CF 연속 흑자 확인")

    # ── FCF Yield (0-40) ──────────────────────────────────────────────────────
    fcf_yields = fd.get("fcf_yields_3y", [])
    cur_yield = fd.get("current_fcf_yield")

    if cur_yield is not None and len(fcf_yields) >= 2:
        past = fcf_yields[1:]
        avg = sum(past) / len(past)
        std = _std(past)
        if std > 0 and cur_yield > avg + 1.5 * std:
            fcf_score = 40
            reasons.append(f"FCF 수익률 {cur_yield:.1%} — 3년 평균 대비 +1.5σ 극단 저평가")
        elif cur_yield > avg and cur_yield > 0.03:
            fcf_score = 28
            reasons.append(f"FCF 수익률 {cur_yield:.1%} — 역사적 평균 상회")
        elif cur_yield > 0.05:
            fcf_score = 20
        elif cur_yield > 0.02:
            fcf_score = 12
        elif cur_yield > 0:
            fcf_score = 5
        else:
            fcf_score = 0
    elif cur_yield is not None:
        if cur_yield > 0.06:
            fcf_score = 24
            reasons.append(f"FCF 수익률 {cur_yield:.1%}")
        elif cur_yield > 0.03:
            fcf_score = 14
        elif cur_yield > 0:
            fcf_score = 6
        else:
            fcf_score = 0
    else:
        fcf_score = 0

    fcf_score = min(40, max(0, fcf_score))

    # ── Liquidity: Current Ratio (0-20) ──────────────────────────────────────
    # Replaces net_cash_ratio; Current Ratio > 1.2 = healthy short-term liquidity
    cr = fd.get("current_ratio")
    if cr is not None:
        if cr >= 2.5:
            liq_score = 20
            reasons.append(f"유동비율 {cr:.1f}x — 강력한 단기 유동성")
        elif cr >= 1.8:
            liq_score = 15
            reasons.append(f"유동비율 {cr:.1f}x — 양호한 유동성")
        elif cr >= 1.2:
            liq_score = 10
        elif cr >= 1.0:
            liq_score = 4
        else:
            liq_score = 0  # current liabilities > current assets = risk
    else:
        liq_score = 7  # neutral / unknown

    liq_score = min(20, max(0, liq_score))

    # ── Accruals (0-20) ───────────────────────────────────────────────────────
    acc_ok = fd.get("accruals_ok")
    if acc_ok is True:
        acc_score = 20
        reasons.append("발생액 음수 — 현금이익이 회계이익 상회 (earnings quality ↑)")
    elif acc_ok is False:
        acc_score = 0
    else:
        acc_score = 10

    # ── Quality Growth: AR & Inventory vs Revenue growth (0-10) ──────────────
    ar_gr = fd.get("ar_growth")    # AR YoY growth (float | None)
    inv_gr = fd.get("inv_growth")  # Inventory YoY growth (float | None)
    rev_gr = fd.get("rev_growth")  # Revenue YoY growth (float | None)

    if rev_gr is None:
        qg_score = 5  # can't assess → neutral
    elif rev_gr <= 0:
        # Revenue declining: AR/inv should also decline
        ar_ok  = ar_gr  is None or ar_gr  < 0
        inv_ok = inv_gr is None or inv_gr < 0
        if ar_ok and inv_ok:
            qg_score = 5
        else:
            qg_score = 0
    else:
        threshold = rev_gr + 0.10  # 10% tolerance
        ar_ok  = ar_gr  is None or ar_gr  <= threshold
        inv_ok = inv_gr is None or inv_gr <= threshold
        if ar_ok and inv_ok:
            qg_score = 10
            if ar_gr is not None or inv_gr is not None:
                worst = max(v for v in [ar_gr, inv_gr] if v is not None)
                reasons.append(
                    f"매출채권·재고 증가율({worst:.0%}) ≤ 매출 증가율({rev_gr:.0%}) — 이익 품질 양호"
                )
        elif ar_ok or inv_ok:
            qg_score = 5
        else:
            qg_score = 0
            reasons.append("매출채권·재고 급증 — 분식 또는 수요 둔화 가능성")

    qg_score = min(10, max(0, qg_score))

    # ── Shareholder Yield: Dividend + Buyback (0-10) ─────────────────────────
    div_yield   = fd.get("dividend_yield")  or 0.0
    buyback_yield = fd.get("buyback_yield") or 0.0
    sh_yield = div_yield + buyback_yield

    if sh_yield >= 0.06:
        sy_score = 10
        reasons.append(f"주주환원 수익률 {sh_yield:.1%} — 배당+자사주 매입")
    elif sh_yield >= 0.04:
        sy_score = 7
    elif sh_yield >= 0.02:
        sy_score = 4
    elif sh_yield >= 0.005:
        sy_score = 2
    else:
        sy_score = 1  # growth stocks: not penalized

    sy_score = min(10, max(0, sy_score))

    total = min(100.0, safety_score + fcf_score + liq_score + acc_score + qg_score + sy_score)

    breakdown = {
        "safety": {
            "score": round(safety_score, 1), "max": 20, "value": None,
        },
        "fcf_yield": {
            "score": round(fcf_score, 1), "max": 40,
            "value": round(cur_yield * 100, 2) if cur_yield is not None else None,
        },
        "liquidity": {
            "score": round(liq_score, 1), "max": 20,
            "value": round(cr, 2) if cr is not None else None,
        },
        "accruals": {
            "score": round(acc_score, 1), "max": 20, "value": None,
        },
        "quality_growth": {
            "score": round(qg_score, 1), "max": 10,
            "value": round(rev_gr * 100, 1) if rev_gr is not None else None,
        },
        "shareholder_yield": {
            "score": round(sy_score, 1), "max": 10,
            "value": round(sh_yield * 100, 2) if sh_yield > 0 else None,
        },
    }
    return round(total, 1), breakdown, reasons


# ── Module 3: Technical Score (0-100) ────────────────────────────────────────

def score_technical(
    history: list[dict],
    benchmark: list[dict] | None = None,
) -> tuple[float, dict, list[str]]:
    """
    history/benchmark: list of {"date","open","high","low","close","volume"}
    Returns (score 0-100, breakdown, reasons).
    """
    reasons: list[str] = []

    empty_bd = {
        "ma_convergence":    {"score": 0, "max": 35, "value": None},
        "volume_explosion":  {"score": 0, "max": 35, "value": None},
        "relative_strength": {"score": 0, "max": 30, "value": None},
    }

    if not history or len(history) < 60:
        return 0.0, empty_bd, ["차트 데이터 부족 (60일 미만)"]

    closes = [d["close"] for d in history]
    volumes = [d["volume"] for d in history]

    # ── 1. MA Convergence + Bollinger Band Squeeze (0-35) ───────────────────
    ma_score = 0
    spread = None

    if len(closes) >= 120:
        ma20  = sum(closes[-20:])  / 20
        ma60  = sum(closes[-60:])  / 60
        ma120 = sum(closes[-120:]) / 120
        mn = min(ma20, ma60, ma120)
        spread = (max(ma20, ma60, ma120) - mn) / mn * 100 if mn > 0 else 999.0

        if spread <= 1.5:
            ma_score = 25
            reasons.append(f"이평선 극도 수렴 {spread:.1f}% — 대형 이탈 임박")
        elif spread <= 3.0:
            ma_score = 20
            reasons.append(f"이평선 수렴 {spread:.1f}%")
        elif spread <= 5.0:
            ma_score = 13
        elif spread <= 8.0:
            ma_score = 6
        else:
            ma_score = max(0, 6 - (spread - 8) * 0.5)

    # ── Bollinger Band Width squeeze bonus (+0~10) ──────────────────────────
    bb_bonus = 0
    current_bbw = None
    if len(closes) >= 20:
        # Rolling 20-day BB widths (4σ / MA) for the entire history
        bb_widths: list[float] = []
        for i in range(20, len(closes) + 1):
            window = closes[i - 20:i]
            mn20 = sum(window) / 20
            if mn20 > 0:
                sd = _std(window)
                bb_widths.append((4 * sd / mn20) * 100)

        if bb_widths:
            current_bbw = bb_widths[-1]
            hist = bb_widths[:-1]
            if len(hist) >= 20:
                pct_rank = sum(1 for w in hist if current_bbw <= w) / len(hist)
                # pct_rank near 1.0 = current width is lower than almost all history = squeeze
                if pct_rank >= 0.95:
                    bb_bonus = 10
                    reasons.append(
                        f"볼린저 밴드 폭 {current_bbw:.1f}% — 1년 기준 최저 수준 (에너지 압축)"
                    )
                elif pct_rank >= 0.80:
                    bb_bonus = 5
                    reasons.append(f"볼린저 밴드 폭 수축 {current_bbw:.1f}%")

    ma_score = min(35, max(0, ma_score + bb_bonus))

    # ── 2. Volume Explosion: best of last 5 days vs 60-day avg (0-35) ────────
    if len(volumes) >= 65:
        avg60_vol = sum(volumes[-65:-5]) / 60
    else:
        avg60_vol = sum(volumes[:-5]) / max(1, len(volumes) - 5) if len(volumes) > 5 else 0

    vol_score = 0
    best_ratio = 0.0
    if avg60_vol > 0:
        recent5 = history[-5:]
        for d in recent5:
            ratio = d["volume"] / avg60_vol * 100
            if ratio > best_ratio:
                best_ratio = ratio
            if ratio >= 400 and d["close"] > d["open"]:
                vol_score = 35
                reasons.append(f"거래량 폭발 {ratio:.0f}% — 대량 장대양봉 (5일 이내)")
            elif ratio >= 300 and d["close"] > d["open"]:
                vol_score = max(vol_score, 24)
            elif ratio >= 200:
                vol_score = max(vol_score, 14)
            elif ratio >= 150:
                vol_score = max(vol_score, 7)

    vol_score = min(35, max(0, vol_score))

    # ── 3. Relative Strength vs NASDAQ benchmark (0-30) ──────────────────────
    rs_score = 15  # neutral when no benchmark
    rs_val: float | None = None

    if benchmark and len(benchmark) >= 63 and len(closes) >= 63:
        stock_ret = (closes[-1] - closes[-63]) / closes[-63] * 100
        bench_c = [d["close"] for d in benchmark]
        if len(bench_c) >= 63 and bench_c[-63] > 0:
            bench_ret = (bench_c[-1] - bench_c[-63]) / bench_c[-63] * 100
            rs_val = stock_ret - bench_ret
            if rs_val >= 25:
                rs_score = 30
                reasons.append(f"상대 강도 +{rs_val:.1f}%p (3개월, NASDAQ 대비)")
            elif rs_val >= 12:
                rs_score = 22
            elif rs_val >= 0:
                rs_score = 15
            elif rs_val >= -10:
                rs_score = 7
            else:
                rs_score = 0

    rs_score = min(30, max(0, rs_score))
    total = min(100.0, ma_score + vol_score + rs_score)

    breakdown = {
        "ma_convergence": {
            "score": round(ma_score, 1), "max": 35,
            "value": round(spread, 1) if spread is not None else None,
        },
        "volume_explosion": {
            "score": round(vol_score, 1), "max": 35,
            "value": round(best_ratio, 0) if best_ratio > 0 else None,
        },
        "relative_strength": {
            "score": round(rs_score, 1), "max": 30,
            "value": round(rs_val, 1) if rs_val is not None else None,
        },
    }
    return round(total, 1), breakdown, reasons


# ── Hybrid Final Score ────────────────────────────────────────────────────────

def calculate_score(
    metrics: dict,
    sector_averages: dict | None = None,
    financial_data: dict | None = None,
    history: list[dict] | None = None,
    benchmark: list[dict] | None = None,
    narrative_keywords: list[str] | None = None,
) -> tuple[float, dict, str]:
    """
    Hybrid score: Fundamental (50%) + Narrative (30%) + Technical (20%).
    Merges metrics-level data (current_ratio, dividend_yield, rev_growth) into fd
    so score_fundamental can access them without changing its signature.
    """
    from narrative import score_narrative

    # Merge metric-level fields into fd for score_fundamental
    fd = {
        **(financial_data or {}),
        "current_ratio":  metrics.get("current_ratio"),
        "dividend_yield": metrics.get("dividend_yield"),
        "rev_growth":     metrics.get("revenue_growth"),
    }

    hist = history or []
    kw   = narrative_keywords or []

    f_score, f_bd, f_reasons = score_fundamental(fd)
    n_score, n_bd, n_reasons = score_narrative(
        sector=metrics.get("sector", ""),
        industry=metrics.get("industry", ""),
        current_price=metrics.get("current_price"),
        target_price=metrics.get("target_mean_price"),
        analyst_count=int(metrics.get("analyst_count") or 0),
        keywords=kw,
    )
    t_score, t_bd, t_reasons = score_technical(hist, benchmark)

    total = round(0.5 * f_score + 0.3 * n_score + 0.2 * t_score, 1)

    breakdown = {**f_bd, **n_bd, **t_bd}

    all_reasons = f_reasons + n_reasons + t_reasons
    if not all_reasons:
        all_reasons = ["하이브리드 퀀트 분석 완료"]

    reasoning = " · ".join(all_reasons[:6])
    return total, breakdown, reasoning


def compute_sector_averages(stocks: list[dict]) -> dict:
    """Stub — kept for backward compatibility."""
    return {}


# ── Utility ───────────────────────────────────────────────────────────────────

def _std(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    avg = sum(vals) / len(vals)
    return math.sqrt(sum((v - avg) ** 2 for v in vals) / len(vals))
