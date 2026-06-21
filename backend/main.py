import logging
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import (
    init_db, get_stocks, get_stock,
    get_counts, get_snapshots,
)
from collector import fetch_price_history

logger = logging.getLogger(__name__)

# ── Benchmark cache (1-day TTL) ───────────────────────────────────────────────
_benchmark_cache: list = []
_benchmark_date = None


def _get_benchmark() -> list:
    global _benchmark_cache, _benchmark_date
    today = datetime.now().date()
    if _benchmark_date == today and _benchmark_cache:
        return _benchmark_cache
    from collector import fetch_benchmark_history
    _benchmark_cache = fetch_benchmark_history("1y")
    _benchmark_date = today
    return _benchmark_cache


# ── Scheduled jobs ────────────────────────────────────────────────────────────

def _job_nasdaq():
    logger.info("=== 스케줄러: NASDAQ 수집 시작 ===")
    try:
        from collect import collect_nasdaq
        collect_nasdaq()
        logger.info("=== 스케줄러: NASDAQ 수집 완료 ===")
    except Exception as e:
        logger.error(f"스케줄러 NASDAQ 오류: {e}")


def _job_kospi():
    logger.info("=== 스케줄러: KOSPI 수집 시작 ===")
    try:
        from collect import collect_kospi
        collect_kospi()
        logger.info("=== 스케줄러: KOSPI 수집 완료 ===")
    except Exception as e:
        logger.error(f"스케줄러 KOSPI 오류: {e}")


_scheduler = BackgroundScheduler(timezone="Asia/Seoul")
_scheduler.add_job(_job_nasdaq, CronTrigger(hour=7,  minute=0), id="nasdaq_daily")
_scheduler.add_job(_job_kospi,  CronTrigger(hour=16, minute=0), id="kospi_daily")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _scheduler.start()
    logger.info("스케줄러 시작 — NASDAQ 매일 07:00 / KOSPI 매일 16:00 (KST)")
    yield
    _scheduler.shutdown(wait=False)
    logger.info("스케줄러 종료")


app = FastAPI(title="Investment Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Status ────────────────────────────────────────────────────────────────────

@app.get("/api/status")
async def status():
    counts = get_counts()
    snapshots = get_snapshots()

    def fmt_snapshot(s: dict | None) -> dict | None:
        if not s:
            return None
        return {
            "collected_at": s["collected_at"],
            "stock_count": s["stock_count"],
            "history_count": s["history_count"],
        }

    return {
        "nasdaq_stocks": counts.get("nasdaq", 0),
        "kospi_stocks": counts.get("kospi", 0),
        "snapshots": {
            "nasdaq": fmt_snapshot(snapshots.get("nasdaq")),
            "kospi": fmt_snapshot(snapshots.get("kospi")),
        },
    }


# ── Stocks ────────────────────────────────────────────────────────────────────

@app.get("/api/stocks")
async def list_stocks(market: Optional[str] = None, sector: Optional[str] = None, limit: int = 200):
    return get_stocks(market=market, sector=sector)[:limit]


@app.get("/api/stocks/{ticker}")
async def stock_detail(ticker: str):
    stock = get_stock(ticker)
    if not stock:
        raise HTTPException(404, "Stock not found")
    return stock


@app.get("/api/stocks/{ticker}/history")
async def stock_history(ticker: str, period: str = "1y"):
    stock = get_stock(ticker)
    market = stock["market"] if stock else "nasdaq"
    return fetch_price_history(ticker, market, period)


# ── Top pick ─────────────────────────────────────────────────────────────────

@app.get("/api/top-pick")
async def top_pick(market: Optional[str] = "nasdaq"):
    """
    Return the single highest-scored stock (score >= 65) for the given market.
    Stocks are already sorted by score DESC from get_stocks().
    """
    stocks = get_stocks(market=market)
    qualified = [s for s in stocks if s.get("score", 0) >= 65]
    if not qualified:
        qualified = stocks[:1]  # fallback: best available
    if not qualified:
        raise HTTPException(404, "분석 데이터가 없습니다")
    return qualified[0]


# ── On-demand analysis ────────────────────────────────────────────────────────

@app.get("/api/analyze/{ticker}")
def analyze_stock(ticker: str):
    """
    Real-time analysis for any ticker not in the pre-collected DB.
    Falls back to DB cache if the stock was collected within the last 24 h.
    Runs in a thread (def, not async) to avoid blocking the event loop.
    """
    ticker = ticker.upper().strip()

    # Return DB cache if fresh enough
    existing = get_stock(ticker)
    if existing:
        try:
            updated = datetime.fromisoformat(existing.get("updated_at", "2000-01-01"))
            if (datetime.now() - updated).total_seconds() < 24 * 3600:
                return existing
        except Exception:
            return existing

    from collector import fetch_us_metrics, fetch_financial_data
    from scorer import calculate_score
    from narrative import extract_narrative_keywords

    m = fetch_us_metrics(ticker)
    if not m:
        raise HTTPException(404, f"티커 '{ticker}'를 찾을 수 없습니다. 정확한 티커 심볼을 입력해 주세요.")

    fin = fetch_financial_data(ticker, m.get("market_cap"))
    hist = fetch_price_history(ticker, "nasdaq", "1y")
    benchmark = _get_benchmark()
    keywords = extract_narrative_keywords()

    score, breakdown, reasoning = calculate_score(
        metrics=m,
        financial_data=fin,
        history=hist,
        benchmark=benchmark,
        narrative_keywords=keywords,
    )

    return {
        "ticker": ticker,
        "market": "nasdaq",
        "name": m["name"],
        "sector": m.get("sector", "Unknown"),
        "industry": m.get("industry", "Unknown"),
        "data": m,
        "score": score,
        "score_breakdown": breakdown,
        "reasoning": reasoning,
        "updated_at": datetime.now().isoformat(),
    }


# ── Sectors ───────────────────────────────────────────────────────────────────

@app.get("/api/sectors")
async def sectors(market: Optional[str] = None):
    stocks = get_stocks(market=market)
    bucket: dict[str, list] = {}
    for s in stocks:
        sec = s.get("sector") or "Unknown"
        bucket.setdefault(sec, []).append(s)
    return {
        sec: sorted(lst, key=lambda x: x["score"], reverse=True)[:10]
        for sec, lst in sorted(bucket.items())
    }
