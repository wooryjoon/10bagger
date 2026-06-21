import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "data", "stocks.db"),
)


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
            updated_at TEXT
        )
    """)
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
