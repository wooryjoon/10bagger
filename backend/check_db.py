import sqlite3, json
conn = sqlite3.connect("data/stocks.db")
cur = conn.cursor()

cur.execute("SELECT market, COUNT(*) FROM stocks GROUP BY market")
print("=== 종목 수 ===")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}개")

cur.execute("SELECT market, MAX(updated_at) FROM stocks GROUP BY market")
print("\n=== 최근 업데이트 ===")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.execute("SELECT ticker, score, score_breakdown FROM stocks WHERE market='nasdaq' ORDER BY score DESC LIMIT 3")
print("\n=== NASDAQ 상위 3개 ===")
for row in cur.fetchall():
    bd = json.loads(row[2]) if row[2] else {}
    print(f"  {row[0]}: 점수={row[1]:.1f}, breakdown keys={list(bd.keys())}")

conn.close()
