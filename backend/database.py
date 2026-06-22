import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "data", "stocks.db"),
)
RUN_LOG_PATH = os.path.join(os.path.dirname(DB_PATH), "run_log.json")
_RUN_LOG_MAX = 50


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            ticker TEXT PRIMARY KEY,
            market TEXT NOT NULL,
            name TEXT,
            sector TEXT,
            industry TEXT,
            data TEXT,
            score REAL,
            score_breakdown TEXT,
            reasoning TEXT,
            ai_comment TEXT,
            stage5_score REAL,
            stage5_breakdown TEXT,
            investment_tier INTEGER,
            updated_at TEXT
        )
    """)
    # Migrate existing DBs incrementally
    for col, definition in [
        ("ai_comment",       "TEXT"),
        ("stage5_score",     "REAL"),
        ("stage5_breakdown", "TEXT"),
        ("investment_tier",  "INTEGER"),
    ]:
        try:
            c.execute(f"ALTER TABLE stocks ADD COLUMN {col} {definition}")
            conn.commit()
        except Exception:
            pass
    c.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            market TEXT PRIMARY KEY,
            collected_at TEXT,
            stock_count INTEGER,
            history_count INTEGER
        )
    """)
    conn.commit()
    conn.close()


def upsert_stock(ticker, market, name, sector, industry, data, score, score_breakdown, reasoning):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO stocks
        (ticker, market, name, sector, industry, data, score, score_breakdown, reasoning, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticker, market, name, sector, industry,
        json.dumps(data, ensure_ascii=False),
        score,
        json.dumps(score_breakdown, ensure_ascii=False),
        reasoning,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def upsert_ai_comment(ticker: str, comment: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE stocks SET ai_comment = ? WHERE ticker = ?", (comment, ticker))
    conn.commit()
    conn.close()


def upsert_stage5(ticker: str, stage5_score: float, stage5_breakdown: dict, investment_tier: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE stocks SET stage5_score = ?, stage5_breakdown = ?, investment_tier = ? WHERE ticker = ?",
        (stage5_score, json.dumps(stage5_breakdown, ensure_ascii=False), investment_tier, ticker),
    )
    conn.commit()
    conn.close()


def get_stocks(market=None, sector=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM stocks WHERE 1=1"
    params = []
    if market:
        query += " AND market = ?"
        params.append(market)
    if sector:
        query += " AND sector = ?"
        params.append(sector)
    query += " ORDER BY score DESC"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        d["data"] = json.loads(d["data"])
        d["score_breakdown"] = json.loads(d["score_breakdown"])
        d.setdefault("ai_comment", None)
        d.setdefault("stage5_score", None)
        d.setdefault("investment_tier", None)
        sb = d.get("stage5_breakdown")
        d["stage5_breakdown"] = json.loads(sb) if sb else None
        result.append(d)
    return result


def get_stock(ticker):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM stocks WHERE ticker = ?", (ticker,))
    row = c.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["data"] = json.loads(d["data"])
        d["score_breakdown"] = json.loads(d["score_breakdown"])
        d.setdefault("ai_comment", None)
        d.setdefault("stage5_score", None)
        d.setdefault("investment_tier", None)
        sb = d.get("stage5_breakdown")
        d["stage5_breakdown"] = json.loads(sb) if sb else None
        return d
    return None



def get_counts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT market, COUNT(*) FROM stocks GROUP BY market")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def record_snapshot(market: str, stock_count: int, history_count: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO snapshots (market, collected_at, stock_count, history_count)
        VALUES (?, ?, ?, ?)
    """, (market, datetime.now().isoformat(), stock_count, history_count))
    conn.commit()
    conn.close()


def record_run_log(
    market: str,
    status: str,
    stocks: int = 0,
    duration_sec: int = 0,
    error_msg: str | None = None,
):
    """Append one run entry to run_log.json. Keeps last _RUN_LOG_MAX entries."""
    entry = {
        "ts":           datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market":       market,
        "status":       status,
        "stocks":       stocks,
        "duration_sec": duration_sec,
        "error":        error_msg,
    }
    try:
        with open(RUN_LOG_PATH, encoding="utf-8") as f:
            entries: list = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []
    entries.append(entry)
    entries = entries[-_RUN_LOG_MAX:]
    os.makedirs(os.path.dirname(RUN_LOG_PATH), exist_ok=True)
    with open(RUN_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def get_run_log(limit: int = 20) -> list[dict]:
    """Return most-recent entries first."""
    try:
        with open(RUN_LOG_PATH, encoding="utf-8") as f:
            entries: list = json.load(f)
        return list(reversed(entries))[:limit]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_snapshots() -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM snapshots")
        return {r["market"]: dict(r) for r in c.fetchall()}
    except Exception:
        return {}
    finally:
        conn.close()
