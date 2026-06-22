"""
Claude AI Narrative Commentary
Generates per-stock AI comments assessing alignment with global investment narratives.
"""

from __future__ import annotations
import os


def generate_ai_comment(
    ticker: str,
    name: str,
    sector: str,
    industry: str,
    score: float,
    data: dict,
) -> str:
    """
    Calls Claude API to assess whether this stock aligns with global investment narratives.
    Returns a 2-3 sentence Korean comment, or empty string on failure / no API key.
    """
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
        return ""

    def _fmt(v, mult: float = 1, dec: int = 1, suffix: str = "") -> str:
        if v is None:
            return "N/A"
        return f"{v * mult:.{dec}f}{suffix}"

    pe         = _fmt(data.get("pe_ratio"),         dec=1, suffix="x")
    pb         = _fmt(data.get("pb_ratio"),          dec=2, suffix="x")
    roe        = _fmt(data.get("roe"),               mult=100, dec=1, suffix="%")
    rev_growth = _fmt(data.get("revenue_growth"),    mult=100, dec=1, suffix="%")
    op_margin  = _fmt(data.get("operating_margin"),  mult=100, dec=1, suffix="%")

    prompt = (
        f"다음 기업이 현재 글로벌 투자 내러티브에 부합하는지 2~3문장으로 간결하게 평가해 주세요.\n\n"
        f"기업 정보:\n"
        f"- 티커/기업명: {ticker} / {name}\n"
        f"- 섹터/산업: {sector} / {industry}\n"
        f"- 퀀트 종합점수: {score:.1f}/100 (펀더멘탈 50% + 기술적 분석 50%)\n"
        f"- 주요 지표: PER {pe}, PBR {pb}, ROE {roe}, 매출성장 {rev_growth}, 영업이익률 {op_margin}\n\n"
        f"2025~2026년 현재 글로벌 주요 투자 테마(AI 인프라·반도체, 방산·우주, 에너지전환·원전, "
        f"바이오·GLP-1, 사이버보안, 데이터센터 등)와의 연관성과, "
        f"이 기업이 현재 시장에서 주목받을 수 있는 이유 또는 주의할 리스크를 한국어로 작성해 주세요."
    )

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as ex:
        print(f"  [AI COMMENT] {ticker} 오류: {ex}")
        return ""
