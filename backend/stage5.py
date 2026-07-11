"""
Stage 5: Deep Analysis — Insider Activity, Institutional Flow, News Sentiment
Computed only for the top 10 stocks after Stage 1–3 scoring.

Bonus scoring (max 15):
  Insider Activity  0–5  (6-month net buy ratio)
  Institutional     0–5  (institutional ownership %)
  News Sentiment    0–5  (contrarian: extreme pessimism = buy signal)
"""
from __future__ import annotations
from datetime import datetime, timedelta


# 구조적 악재 키워드 — 이 단어가 헤드라인에 있으면 역발상 점수 무효
_STRUCTURAL_RISK = [
    'fraud', 'bankruptcy', 'bankrupt', 'delist', 'delisting', 'criminal',
    'sec investigation', 'going concern', 'chapter 11', 'chapter11',
    'ponzi', 'embezzlement', 'securities fraud', 'accounting irregularity',
    'class action', 'restatement', 'material weakness',
]

_POS = [
    'beat', 'exceed', 'record', 'surge', 'rally', 'upgrade', 'buy', 'strong',
    'growth', 'profit', 'gain', 'rise', 'outperform', 'momentum', 'bullish',
    'positive', 'expand', 'milestone', 'launch', 'partnership',
]
_NEG = [
    'miss', 'fall', 'drop', 'decline', 'weak', 'loss', 'cut', 'downgrade', 'sell',
    'warning', 'risk', 'concern', 'disappointing', 'below', 'layoff', 'lawsuit',
    'investigation', 'fraud', 'fine', 'penalty', 'bearish', 'probe', 'recall',
]


def _sentiment(text: str) -> float:
    """Polarity –1 to +1. Uses TextBlob if available, else keyword heuristic."""
    try:
        from textblob import TextBlob  # type: ignore
        return TextBlob(text).sentiment.polarity
    except ImportError:
        pass
    t = text.lower()
    pos = sum(1 for w in _POS if w in t)
    neg = sum(1 for w in _NEG if w in t)
    total = pos + neg
    return (pos - neg) / total if total > 0 else 0.0


def _news_title(item: dict) -> str:
    """Handle both old yfinance format (item['title']) and new (item['content']['title'])."""
    if item.get('title'):
        return str(item['title'])
    content = item.get('content')
    if isinstance(content, dict):
        return str(content.get('title', ''))
    return ''


def _news_url(item: dict) -> str:
    """Extract article URL — new format: content.canonicalUrl.url, old format: item['link']."""
    content = item.get('content')
    if isinstance(content, dict):
        canonical = content.get('canonicalUrl') or content.get('clickThroughUrl')
        if isinstance(canonical, dict):
            return str(canonical.get('url', ''))
    return str(item.get('link', ''))


def _news_ts(item: dict) -> float:
    """Extract publish timestamp — old format: providerPublishTime (int), new: content.pubDate (ISO)."""
    ts = item.get('providerPublishTime')
    if ts:
        return float(ts)
    content = item.get('content')
    if isinstance(content, dict):
        pub = content.get('pubDate') or content.get('displayTime', '')
        if pub:
            try:
                dt = datetime.fromisoformat(str(pub).replace('Z', '+00:00'))
                return dt.timestamp()
            except Exception:
                pass
    return 0.0


def fetch_stage5_data(ticker: str) -> dict:
    """Return insider / institutional / news sentiment data for a US-listed ticker."""
    import yfinance as yf

    result: dict = {
        "insider_buy_ratio":   None,
        "insider_buy_count":   0,
        "insider_sell_count":  0,
        "inst_ownership_pct":  None,
        "sentiment_avg":       None,
        "news_count":          0,
        "headlines":           [],
        "structural_risk":     False,  # 사기·파산 등 구조적 악재 감지 여부
    }

    try:
        t = yf.Ticker(ticker)

        # ── Insider Transactions (last 6 months) ─────────────────────────────
        # Transaction column is often empty; actual buy/sell is in the Text column
        try:
            import pandas as pd
            txns = t.insider_transactions
            if txns is not None and not txns.empty:
                # Detect date column
                date_col = next((c for c in txns.columns if 'date' in c.lower()), None)
                # Prefer Text column for buy/sell detection; fall back to Transaction
                text_col = 'Text' if 'Text' in txns.columns else None
                type_col = next((c for c in txns.columns if c.lower() == 'transaction'), None)

                recent = txns
                if date_col:
                    cutoff = pd.Timestamp(datetime.now() - timedelta(days=180), tz='UTC')
                    dt = pd.to_datetime(txns[date_col], errors='coerce', utc=True)
                    mask = dt >= cutoff
                    if mask.any():
                        recent = txns[mask]

                if not recent.empty:
                    search_col = text_col or type_col
                    shares_col = 'Shares' if 'Shares' in recent.columns else None
                    if search_col:
                        vals      = recent[search_col].astype(str).str.lower()
                        buy_mask  = vals.str.contains('purchase|buy|acquisition')
                        sell_mask = vals.str.contains('sale|sell')
                        result["insider_buy_count"]  = int(buy_mask.sum())
                        result["insider_sell_count"] = int(sell_mask.sum())
                        # Weight by shares traded, not transaction count
                        if shares_col:
                            buy_sh  = float(recent.loc[buy_mask,  shares_col].fillna(0).sum())
                            sell_sh = float(recent.loc[sell_mask, shares_col].fillna(0).sum())
                            total   = buy_sh + sell_sh
                        else:
                            buy_sh  = float(result["insider_buy_count"])
                            sell_sh = float(result["insider_sell_count"])
                            total   = buy_sh + sell_sh
                        if total > 0:
                            result["insider_buy_ratio"] = round(buy_sh / total, 3)
        except Exception:
            pass

        # ── Institutional Ownership % ─────────────────────────────────────────
        # major_holders index names: insidersPercentHeld, institutionsPercentHeld, ...
        try:
            mh = t.major_holders
            if mh is not None and not mh.empty:
                for idx_name in mh.index:
                    idx_str = str(idx_name).lower()
                    if 'institutionspercent' in idx_str and 'float' not in idx_str:
                        val = mh.loc[idx_name].iloc[0]
                        try:
                            f = float(val)
                            if 0 < f <= 1.0:
                                result["inst_ownership_pct"] = round(f, 4)
                            elif 1.0 < f <= 100.0:
                                result["inst_ownership_pct"] = round(f / 100, 4)
                        except (ValueError, TypeError):
                            pass
                        break
                # Fallback: search by value pattern if index-based lookup failed
                if result["inst_ownership_pct"] is None:
                    for i in range(len(mh)):
                        row_text = str(mh.index[i]).lower() if hasattr(mh.index, '__getitem__') else ''
                        if 'institution' in row_text and 'float' not in row_text:
                            for v in mh.iloc[i].values:
                                s = str(v).strip()
                                try:
                                    if '%' in s:
                                        result["inst_ownership_pct"] = round(float(s.replace('%', '')) / 100, 4)
                                        break
                                    f = float(s)
                                    if 0 < f <= 1.0:
                                        result["inst_ownership_pct"] = round(f, 4)
                                        break
                                    if 1.0 < f <= 100.0:
                                        result["inst_ownership_pct"] = round(f / 100, 4)
                                        break
                                except (ValueError, AttributeError):
                                    continue
                            break
        except Exception:
            pass

        # ── News Sentiment (last 14 days) ─────────────────────────────────────
        try:
            news = t.news or []
            cutoff_ts = (datetime.now() - timedelta(days=14)).timestamp()
            recent_news = [n for n in news if _news_ts(n) >= cutoff_ts]
            if not recent_news:
                recent_news = news[:8]

            headlines = [
                {"title": _news_title(n), "url": _news_url(n)}
                for n in recent_news
                if _news_title(n)
            ]
            result["news_count"] = len(headlines)
            result["headlines"]  = headlines[:4]

            if headlines:
                titles = [h["title"] for h in headlines]
                scores = [_sentiment(t) for t in titles]
                result["sentiment_avg"] = round(sum(scores) / len(scores), 3)
                # 구조적 악재 감지 — 역발상 채점 무효화
                result["structural_risk"] = any(
                    any(w in t.lower() for w in _STRUCTURAL_RISK)
                    for t in titles
                )
        except Exception:
            pass

    except Exception as e:
        print(f"  [ERR stage5] {ticker}: {e}")

    return result


def score_stage5(data: dict) -> tuple[float, dict, list[str]]:
    """
    Returns (bonus 0–15, breakdown dict, reason strings).
    Contrarian framing: bad news + insider buying at bottom = buy signal.
    """
    reasons: list[str] = []

    # ── Insider Activity (0–5) ────────────────────────────────────────────────
    ratio = data.get("insider_buy_ratio")
    buys  = data.get("insider_buy_count", 0)

    if ratio is None:
        ins = 2
    elif ratio >= 0.80 and buys >= 2:
        ins = 5; reasons.append(f"내부자 강력 순매수 {buys}건 ({ratio:.0%}) — 바닥권 확신")
    elif ratio >= 0.60:
        ins = 4; reasons.append(f"내부자 매수 우세 ({ratio:.0%})")
    elif ratio >= 0.40:
        ins = 3
    elif ratio >= 0.20:
        ins = 1
    else:
        ins = 0; reasons.append("내부자 순매도 — 리스크 주의")

    # ── Institutional Ownership (0–5) ─────────────────────────────────────────
    inst = data.get("inst_ownership_pct")

    if inst is None:
        inst_s = 2
    elif inst >= 0.80:
        inst_s = 5; reasons.append(f"기관 보유 {inst:.0%} — 대규모 기관 집중")
    elif inst >= 0.65:
        inst_s = 4; reasons.append(f"기관 보유 {inst:.0%}")
    elif inst >= 0.50:
        inst_s = 3
    elif inst >= 0.30:
        inst_s = 2
    else:
        inst_s = 1

    # ── News Sentiment (0–5) — contrarian: pessimism = undervaluation signal ──
    sent    = data.get("sentiment_avg")
    cnt     = data.get("news_count", 0)
    is_risk = data.get("structural_risk", False)

    if is_risk:
        sent_s = 0; reasons.append("구조적 악재 감지 (사기·파산 관련 뉴스) — 역발상 무효")
    elif sent is None or cnt == 0:
        sent_s = 2
    elif sent <= -0.30:
        sent_s = 5; reasons.append(f"극단 비관론 (감성 {sent:.2f}) — 역발상 매수 기회")
    elif sent <= -0.10:
        sent_s = 4; reasons.append(f"부정적 뉴스 ({sent:.2f}) — 역발상 신호")
    elif sent <= 0.10:
        sent_s = 3
    elif sent <= 0.30:
        sent_s = 2
    else:
        sent_s = 1

    bonus = min(15, ins + inst_s + sent_s)

    bd = {
        "insider_activity":   {
            "score": round(ins, 1),    "max": 5,
            "value": round(ratio * 100, 1) if ratio is not None else None,
        },
        "institutional_flow": {
            "score": round(inst_s, 1), "max": 5,
            "value": round(inst * 100, 1) if inst is not None else None,
        },
        "news_sentiment":     {
            "score": round(sent_s, 1), "max": 5,
            "value": round(sent, 3) if sent is not None else None,
        },
        "headlines": data.get("headlines", []),
    }
    return round(bonus, 1), bd, reasons
