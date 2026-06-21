"""
Module 2: Global Narrative & Sentiment Analysis
Extracts market theme keywords via Claude, then maps each stock's
sector/industry to those themes and checks analyst consensus reversal.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

# ── Keyword → Sector mapping ──────────────────────────────────────────────────

KEYWORD_SECTOR_MAP: dict[str, list[str]] = {
    "AI": ["Technology", "Communication Services"],
    "Artificial Intelligence": ["Technology", "Communication Services"],
    "AI Bottleneck": ["Technology"],
    "AI Infrastructure": ["Technology", "Utilities", "Industrials"],
    "Memory Shortage": ["Technology"],
    "Semiconductor": ["Technology"],
    "Power Infrastructure": ["Utilities", "Industrials"],
    "Data Center": ["Technology", "Real Estate"],
    "Cloud Computing": ["Technology", "Communication Services"],
    "Cybersecurity": ["Technology"],
    "Electric Vehicle": ["Consumer Cyclical", "Industrials"],
    "Autonomous Driving": ["Technology", "Consumer Cyclical"],
    "Biotech": ["Healthcare"],
    "GLP-1": ["Healthcare"],
    "Obesity": ["Healthcare"],
    "Defense": ["Industrials"],
    "Energy Transition": ["Energy", "Utilities", "Industrials"],
    "Nuclear": ["Utilities", "Energy"],
    "eCommerce": ["Consumer Cyclical", "Communication Services"],
    "Streaming": ["Communication Services"],
    "5G": ["Technology", "Communication Services"],
    "Quantum": ["Technology"],
    "Supply Chain": ["Industrials", "Consumer Cyclical"],
    "Fintech": ["Financial Services", "Technology"],
    "SaaS": ["Technology"],
    "Infrastructure": ["Industrials", "Utilities"],
    "Interest Rate": ["Financial Services", "Real Estate"],
}

# More precise industry-level matching (bonus points)
KEYWORD_INDUSTRY_MAP: dict[str, list[str]] = {
    "AI Bottleneck": ["Semiconductors", "Semiconductor Equipment", "Computer Hardware"],
    "AI Infrastructure": ["Semiconductors", "Software—Infrastructure", "Electrical Equipment"],
    "Memory Shortage": ["Semiconductors—Memory", "Semiconductor Equipment"],
    "Power Infrastructure": ["Utilities—Regulated Electric", "Electrical Equipment"],
    "Data Center": ["Information Technology Services", "Software—Infrastructure"],
    "Cybersecurity": ["Software—Infrastructure", "Software—Application"],
    "GLP-1": ["Drug Manufacturers", "Biotechnology"],
    "Nuclear": ["Utilities—Regulated Electric"],
    "Cloud Computing": ["Software—Infrastructure", "Information Technology Services"],
    "Autonomous Driving": ["Software—Application", "Electronic Components"],
}

DEFAULT_KEYWORDS = [
    "AI Bottleneck", "Memory Shortage", "Power Infrastructure",
    "Cloud Computing", "Cybersecurity",
]

_cached_keywords: list[str] | None = None
_cache_date: object = None


def _market_context() -> str:
    return f"""Date: {datetime.now().strftime('%Y-%m-%d')}

Market Context:
- Fed maintaining higher-for-longer stance; market pricing 1-2 cuts ahead
- AI infrastructure capex accelerating (AWS, Azure, GCP all raised guidance)
- HBM memory demand surging for AI training and inference workloads
- Data center power constraints creating utility/infrastructure bottleneck
- Biotech: GLP-1/obesity pipeline expansions gaining momentum across multiple companies
- Advanced chip export restrictions affecting US-China semiconductor supply chain
- Cybersecurity spend resilient as ransomware and nation-state attacks escalate
- Cloud reacceleration visible across major platforms after prior-year slowdown
- Consumer bifurcation: premium brands holding, mass-market under pressure
- Grid modernization investments increasing (nuclear + renewables)
- Autonomous driving regulatory approvals accelerating in key markets
"""


def extract_narrative_keywords(force: bool = False) -> list[str]:
    """
    Calls Claude to extract 3-5 market theme keywords for the current date.
    Result is cached once per day. Falls back to DEFAULT_KEYWORDS if API key missing.
    """
    global _cached_keywords, _cache_date

    today = datetime.now().date()
    if not force and _cached_keywords and _cache_date == today:
        return _cached_keywords

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            load_dotenv(Path(__file__).parent / ".env")
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        except Exception:
            pass

    if not api_key:
        print("  [NARRATIVE] ANTHROPIC_API_KEY 없음 → 기본 키워드 사용")
        _cached_keywords = DEFAULT_KEYWORDS
        _cache_date = today
        return DEFAULT_KEYWORDS

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": (
                    "다음 시장 컨텍스트에서 향후 6개월 주식 급등을 이끌 핵심 테마 키워드 3~5개를 "
                    "JSON 배열로만 응답하세요. 영어로. 예: [\"AI Bottleneck\", \"Memory Shortage\"]\n\n"
                    + _market_context()
                ),
            }],
        )
        text = resp.content[0].text.strip()
        s, e = text.find("["), text.rfind("]") + 1
        if s >= 0 and e > s:
            kw = json.loads(text[s:e])
            _cached_keywords = [str(k) for k in kw[:5]]
            _cache_date = today
            print(f"  [NARRATIVE] Claude 추출 키워드: {_cached_keywords}")
            return _cached_keywords
    except Exception as ex:
        print(f"  [NARRATIVE] Claude API 오류: {ex}")

    _cached_keywords = DEFAULT_KEYWORDS
    _cache_date = today
    return DEFAULT_KEYWORDS


def score_narrative(
    sector: str,
    industry: str,
    current_price: float | None,
    target_price: float | None,
    analyst_count: int,
    keywords: list[str],
) -> tuple[float, dict, list[str]]:
    """
    Returns (score 0-100, breakdown dict, reasons list).

    keyword_match (0-60): sector/industry alignment with extracted themes
    consensus     (0-40): analyst target price upside potential
    """
    reasons: list[str] = []
    sector = sector or ""
    industry = industry or ""

    # ── Keyword → Sector/Industry match (0-60) ───────────────────────────────
    kw_score = 0
    matched: list[str] = []
    for kw in keywords:
        hit = False
        for s in KEYWORD_SECTOR_MAP.get(kw, []):
            if s.lower() in sector.lower():
                kw_score += 12
                hit = True
        for ind in KEYWORD_INDUSTRY_MAP.get(kw, []):
            if ind.lower() in industry.lower():
                kw_score += 8
                hit = True
        if hit and kw not in matched:
            matched.append(kw)

    kw_score = min(60, kw_score)
    if matched:
        reasons.append(f"핵심 테마 부합: {', '.join(matched)}")

    # ── Analyst consensus reversal (0-40) ────────────────────────────────────
    con_score = 10  # neutral when no analyst data
    upside_pct: float | None = None

    if target_price and current_price and current_price > 0 and analyst_count >= 3:
        upside_pct = (target_price - current_price) / current_price * 100
        if upside_pct >= 50:
            con_score = 40
        elif upside_pct >= 30:
            con_score = 30
        elif upside_pct >= 15:
            con_score = 20
        elif upside_pct >= 5:
            con_score = 12
        elif upside_pct < -5:
            con_score = 0

        if upside_pct >= 20 and analyst_count >= 5:
            reasons.append(f"애널리스트 컨센서스 +{upside_pct:.0f}% 업사이드 ({analyst_count}명)")

    total = min(100.0, kw_score + con_score)

    breakdown = {
        "keyword_match": {
            "score": round(kw_score, 1), "max": 60, "value": None,
        },
        "consensus": {
            "score": round(con_score, 1), "max": 40,
            "value": round(upside_pct, 1) if upside_pct is not None else None,
        },
    }
    return round(total, 1), breakdown, reasons
