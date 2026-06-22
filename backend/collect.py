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

from database import init_db, upsert_stock, upsert_ai_comment, upsert_stage5, record_snapshot, record_run_log, get_counts, get_stocks
from collector import (
    get_nasdaq200_tickers,
    get_kospi100_tickers,
    fetch_us_metrics,
    fetch_kr_metrics,
    fetch_financial_data,
    fetch_price_history,
)
from scorer import calculate_score, compute_sector_averages
from narrative import generate_ai_comment

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
    log.info("  Fundamental(50%) + Technical(50%)")
    log.info("=" * 60)

    tickers = get_nasdaq200_tickers()
    log.info(f"티커 {len(tickers)}개 확보")

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

    # 섹터별 PSR 평균 계산 (상대 밸류에이션용)
    sector_psr: dict[str, list[float]] = {}
    for _, m in all_metrics:
        sec = m.get("sector") or "Unknown"
        psr = m.get("price_to_sales")
        if psr and isinstance(psr, (int, float)) and psr > 0:
            sector_psr.setdefault(sec, []).append(psr)
    sector_avg_psr = {s: sum(v) / len(v) for s, v in sector_psr.items() if v}
    log.info(f"섹터 PSR 평균: {len(sector_avg_psr)}개 섹터 계산 완료")

    # ── Phase 2: 상세 분석 + 하이브리드 점수 + DB 저장 ───────────────────────
    log.info(f"\n[Phase 2] 하이브리드 점수 산출 + DB 저장 ({len(all_metrics)}개)")
    ok = 0
    for i, (ticker, m) in enumerate(all_metrics, 1):
        try:
            fin = fetch_financial_data(ticker, m.get("market_cap"))
            hist = fetch_price_history(ticker, "nasdaq", "1y")

            score, breakdown, reasoning = calculate_score(
                metrics=m,
                sector_averages=sector_avg_psr,
                financial_data=fin,
                history=hist,
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

    # ── Phase 3: 상위 10개 종목 심층 수급·감성 분석 (Stage 5) ─────────────────
    log.info(f"\n[Phase 3] 상위 10개 종목 심층 수급·감성 분석 (Stage 5)...")
    try:
        from stage5 import fetch_stage5_data, score_stage5

        top10 = get_stocks(market="nasdaq")[:10]
        stage5_results: list[tuple[str, float, float, dict]] = []

        for s in top10:
            try:
                s5data = fetch_stage5_data(s["ticker"])
                bonus, breakdown, reasons = score_stage5(s5data)
                stage5_results.append((s["ticker"], s["score"], bonus, breakdown))
                log.info(
                    f"  {s['ticker']:6}  보너스=+{bonus}/15  enhanced={s['score'] + bonus:.1f}  "
                    + (", ".join(reasons[:2]) if reasons else "중립")
                )
            except Exception as e:
                stage5_results.append((s["ticker"], s["score"], 0.0, {}))
                log.info(f"  {s['ticker']:6}  Stage 5 오류: {e}")
            time.sleep(0.5)

        # Re-rank within top 10 by enhanced score, assign Tier 1/2/3
        stage5_results.sort(key=lambda x: x[1] + x[2], reverse=True)
        for rank, (ticker, base, bonus, breakdown) in enumerate(stage5_results, 1):
            tier = 1 if rank <= 3 else 2 if rank <= 7 else 3
            upsert_stage5(ticker, bonus, breakdown, tier)
            log.info(f"  Tier {tier}: {ticker:6}  enhanced={base + bonus:.1f}")
    except Exception as e:
        log.info(f"  Stage 5 전체 오류: {e}")

    # ── Phase 4: 상위 10개 AI 내러티브 코멘트 ────────────────────────────────
    log.info(f"\n[Phase 4] 상위 10개 종목 AI 내러티브 코멘트 생성 (Claude API)...")
    top10 = get_stocks(market="nasdaq")[:10]
    for s in top10:
        try:
            comment = generate_ai_comment(
                ticker=s["ticker"],
                name=s["name"],
                sector=s.get("sector", ""),
                industry=s.get("industry", ""),
                score=s["score"],
                data=s["data"],
            )
            if comment:
                upsert_ai_comment(s["ticker"], comment)
                log.info(f"  {s['ticker']:6}  AI 코멘트 저장 ({len(comment)}자)")
            else:
                log.info(f"  {s['ticker']:6}  AI 코멘트 없음 (API 키 미설정)")
        except Exception as e:
            log.info(f"  {s['ticker']:6}  AI 코멘트 오류: {e}")
        time.sleep(0.5)


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

    # ── Phase 3: 상위 10개 AI 내러티브 코멘트 ────────────────────────────────
    log.info(f"\n[Phase 3] KOSPI 상위 10개 종목 AI 내러티브 코멘트 생성...")
    top10 = get_stocks(market="kospi")[:10]
    for s in top10:
        try:
            comment = generate_ai_comment(
                ticker=s["ticker"],
                name=s["name"],
                sector=s.get("sector", ""),
                industry=s.get("industry", ""),
                score=s["score"],
                data=s["data"],
            )
            if comment:
                upsert_ai_comment(s["ticker"], comment)
                log.info(f"  {s['ticker']:6}  AI 코멘트 저장 ({len(comment)}자)")
            else:
                log.info(f"  {s['ticker']:6}  AI 코멘트 없음 (API 키 미설정)")
        except Exception as e:
            log.info(f"  {s['ticker']:6}  AI 코멘트 오류: {e}")
        time.sleep(0.5)


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
        _start = time.time()
        _status, _error = "failed", None
        try:
            collect_nasdaq()
            _status = "success"
        except Exception as _e:
            _error = str(_e)
            log.error(f"NASDAQ 수집 오류: {_e}")
        finally:
            record_run_log("nasdaq", _status, get_counts().get("nasdaq", 0), int(time.time() - _start), _error)

    if args.market in ("kospi", "all"):
        _start = time.time()
        _status, _error = "failed", None
        try:
            collect_kospi()
            _status = "success"
        except Exception as _e:
            _error = str(_e)
            log.error(f"KOSPI 수집 오류: {_e}")
        finally:
            record_run_log("kospi", _status, get_counts().get("kospi", 0), int(time.time() - _start), _error)

    log.info("전체 수집 완료")
