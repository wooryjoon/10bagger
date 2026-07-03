"""
Swing trade scoring — stocks with ~10% upside potential.

Signals (2pts each, max 10):
  1. recovery_potential  — 10–35% below 52w high
  2. volume_dryup        — 10d avg volume / 60d avg ≤ 65%
  3. atr_contraction     — 10d ATR / 60d ATR ≤ 70%
  4. ma50_support        — price > MA50 AND 8%+ bounce from 52w low
  5. relative_strength   — 3m return vs QQQ > 0
"""
from __future__ import annotations


def _mean_atr(closes: list[float], n: int) -> float | None:
    if len(closes) < n + 1:
        return None
    return sum(abs(closes[i] - closes[i - 1]) for i in range(-n, 0)) / n


def compute_swing(
    closes: list[float],
    volumes: list[float],
    week52_high: float | None,
    week52_low: float | None,
    qqq_return_3m: float | None = None,
) -> tuple[float, dict]:
    """Return (swing_score 0–10, breakdown dict)."""
    if len(closes) < 60:
        return 0.0, {}

    current = closes[-1]
    bd: dict = {}
    total = 0.0

    # 1. 52주 고점 회복 여력 10–35%
    if week52_high and week52_high > 0 and current > 0:
        pct = (week52_high / current - 1) * 100
        pts = 2 if 10 <= pct <= 35 else 0
        bd["recovery_potential"] = {"score": pts, "max": 2, "value": round(pct, 1)}
        total += pts
    else:
        bd["recovery_potential"] = {"score": 0, "max": 2, "value": None}

    # 2. 거래량 수축 (10d avg / 60d avg)
    if len(volumes) >= 60 and any(v > 0 for v in volumes[-60:]):
        v10 = sum(volumes[-10:]) / 10
        v60 = sum(volumes[-60:]) / 60
        ratio = v10 / v60 if v60 > 0 else 1.0
        pts = 2 if ratio <= 0.65 else (1 if ratio <= 0.80 else 0)
        bd["volume_dryup"] = {"score": pts, "max": 2, "value": round(ratio * 100, 1)}
        total += pts
    else:
        bd["volume_dryup"] = {"score": 0, "max": 2, "value": None}

    # 3. ATR 수축 (10d ATR / 60d ATR)
    atr10 = _mean_atr(closes, 10)
    atr60 = _mean_atr(closes, 60)
    if atr10 and atr60 and atr60 > 0:
        ratio = atr10 / atr60
        pts = 2 if ratio <= 0.70 else (1 if ratio <= 0.85 else 0)
        bd["atr_contraction"] = {"score": pts, "max": 2, "value": round(ratio * 100, 1)}
        total += pts
    else:
        bd["atr_contraction"] = {"score": 0, "max": 2, "value": None}

    # 4. MA50 위 안착 + 52주 저점 대비 +8% 이상 반등
    if len(closes) >= 50:
        ma50 = sum(closes[-50:]) / 50
        bounce = ((current / week52_low) - 1) * 100 if week52_low and week52_low > 0 else None
        above = current > ma50
        good_bounce = bounce is not None and bounce >= 8
        pts = 2 if (above and good_bounce) else (1 if above else 0)
        bd["ma50_support"] = {"score": pts, "max": 2, "value": round(bounce, 1) if bounce is not None else None}
        total += pts
    else:
        bd["ma50_support"] = {"score": 0, "max": 2, "value": None}

    # 5. 상대강도 vs QQQ 3개월
    if len(closes) >= 63:
        stock_ret = (closes[-1] / closes[-63] - 1) * 100
        if qqq_return_3m is not None:
            diff = stock_ret - qqq_return_3m
            pts = 2 if diff > 0 else 0
            bd["relative_strength"] = {"score": pts, "max": 2, "value": round(diff, 1)}
            total += pts
        else:
            bd["relative_strength"] = {"score": 0, "max": 2, "value": None}
    else:
        bd["relative_strength"] = {"score": 0, "max": 2, "value": None}

    return round(total, 1), bd


def swing_reasoning(bd: dict) -> str:
    parts = []
    rp = bd.get("recovery_potential", {})
    if rp.get("score", 0) > 0 and rp.get("value") is not None:
        parts.append(f"고점 -{rp['value']:.0f}%")
    vd = bd.get("volume_dryup", {})
    if vd.get("score", 0) > 0 and vd.get("value") is not None:
        parts.append(f"거래량 {vd['value']:.0f}%")
    ac = bd.get("atr_contraction", {})
    if ac.get("score", 0) > 0:
        parts.append("ATR 수축")
    ms = bd.get("ma50_support", {})
    if ms.get("score", 0) > 0:
        parts.append("MA50 위")
    rs = bd.get("relative_strength", {})
    if rs.get("score", 0) > 0 and rs.get("value") is not None:
        parts.append(f"RS +{rs['value']:.1f}%")
    return " · ".join(parts) if parts else "스윙 후보"
