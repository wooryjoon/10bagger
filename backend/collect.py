"""
Standalone data collection script — run this independently of the FastAPI server.

Usage:
    python collect.py                  # nasdaq + kospi
    python collect.py --market nasdaq
    python collect.py --market kospi

Windows Task Scheduler:
    매일 07:00 → python collect.py --market nasdaq
    매일 16:00 → python collect.py --market kospi
"""

import argparse
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from database import init_db, upsert_stock, record_snapshot
from collector import (
    get_nasdaq200_tickers,
    get_kospi100_tickers,
    fetch_us_metrics,
    fetch_kr_metrics,
    fetch_financial_data,
    fetch_price_history,
    fetch_benchmark_history,
)
from scorer import calculate_score, compute_sector_averages
from narrative import extract_narrative_keywords

# ── Logging: 콘솔 + 파일 동시 출력 ───────────────────────────────────────────
log_path = ROOT / "collect.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ── NASDAQ ────────────────────────────────────────────────────────────────────

def collect_nasdaq():
    log.info("=" * 60)
    log.info("NASDAQ 200 수집 시작 — 하이브리드 퀀트 스크리닝")
    log.info("  Fundamental(50%) + Narrative(30%) + Technical(20%)")
    log.info("=" * 60)

    tickers = get_nasdaq200_tickers()
    log.info(f"티커 {len(tickers)}개 확보")

    # ── 1회성 공통 준비 ───────────────────────────────────────────────────────
    log.info("내러티브 키워드 추출 중 (Claude API)...")
    keywords = extract_narrative_keywords()
    log.info(f"키워드: {keywords}")

    log.info("NASDAQ 벤치마크(^IXIC) 1년 히스토리 수집 중...")
    benchmark = fetch_benchmark_history("1y")
    log.info(f"벤치마크 데이터: {len(benchmark)}일")

    # ── Phase 1: 기본 재무 지표 수집 ─────────────────────────────────────────
    log.info(f"\n[Phase 1] 기본 재무 지표 수집 ({len(tickers)}개 티커)")
    all_metrics: list[tuple[str, dict]] = []
    for i, ticker in enumerate(tickers, 1):
        m = fetch_us_metrics(ticker)
        if m:
            all_metrics.append((ticker, m))
            log.info(f"  [{i:3}/{len(tickers)}] {ticker:6}  ✓ {m['name'][:30]}")
        else:
            log.info(f"  [{i:3}/{len(tickers)}] {ticker:6}  ← 데이터 없음, 건너뜀")
        time.sleep(0.4)

    log.info(f"기본 재무 수집 완료: {len(all_metrics)}/{len(tickers)}")

    # ── Phase 2: 상세 분석 + 하이브리드 점수 + DB 저장 ───────────────────────
    log.info(f"\n[Phase 2] 하이브리드 점수 산출 + DB 저장 ({len(all_metrics)}개)")
    ok = 0
    for i, (ticker, m) in enumerate(all_metrics, 1):
        try:
            # Module 1: Financial statement data
            fin = fetch_financial_data(ticker, m.get("market_cap"))

            # Module 3: Price history for technical analysis
            hist = fetch_price_history(ticker, "nasdaq", "1y")

            score, breakdown, reasoning = calculate_score(
                metrics=m,
                financial_data=fin,
                history=hist,
                benchmark=benchmark,
                narrative_keywords=keywords,
            )

            upsert_stock(
                ticker=ticker,
                market="nasdaq",
                name=m["name"],
                sector=m.get("sector", "Unknown"),
                industry=m.get("industry", "Unknown"),
                data=m,
                score=score,
                score_breakdown=breakdown,
                reasoning=reasoning,
            )
            ok += 1
            log.info(
                f"  [{i:3}/{len(all_metrics)}] {ticker:6}  "
                f"점수={score:5.1f}  {reasoning[:55]}"
            )
        except Exception as e:
            log.info(f"  [{i:3}/{len(all_metrics)}] {ticker:6}  오류: {e}")

        time.sleep(0.3)

    record_snapshot("nasdaq", ok, 0)
    log.info(f"\nNASDAQ 완료 — 종목 {ok}/{len(all_metrics)}개 저장")


# ── KOSPI ─────────────────────────────────────────────────────────────────────

def collect_kospi():
    log.info("=" * 60)
    log.info("KOSPI 100 수집 시작")
    log.info("=" * 60)

    tickers = get_kospi100_tickers()
    if not tickers:
        log.info("KOSPI 티커를 가져오지 못했습니다")
        return

    log.info(f"티커 {len(tickers)}개 확보")

    stock_ok = 0
    for i, krx_ticker in enumerate(tickers, 1):
        log.info(f"  [{i:3}/{len(tickers)}] KS{krx_ticker}  수집 중...")
        m = fetch_kr_metrics(krx_ticker)
        if not m:
            continue

        # KOSPI: 재무제표 데이터 없으므로 narrative + technical만 적용
        score, breakdown, reasoning = calculate_score(m)
        db_ticker = f"KS{krx_ticker}"

        upsert_stock(
            ticker=db_ticker,
            market="kospi",
            name=m["name"],
            sector=m["sector"],
            industry=m["industry"],
            data=m,
            score=score,
            score_breakdown=breakdown,
            reasoning=reasoning,
        )
        stock_ok += 1

        log.info(f"  [{i:3}/{len(tickers)}] {m['name']}  점수={score:.0f}")
        time.sleep(0.5)

    record_snapshot("kospi", stock_ok, 0)
    log.info(f"KOSPI 완료 — 종목 {stock_ok}개 저장")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="하이브리드 퀀트 스크리닝 데이터 수집")
    parser.add_argument(
        "--market",
        choices=["nasdaq", "kospi", "all"],
        default="all",
        help="수집할 시장 (기본값: all)",
    )
    args = parser.parse_args()

    init_db()

    if args.market in ("nasdaq", "all"):
        collect_nasdaq()
    if args.market in ("kospi", "all"):
        collect_kospi()

    log.info("전체 수집 완료")
