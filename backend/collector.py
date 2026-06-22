import math
import re
import time
import requests
import yfinance as yf
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ── NASDAQ tickers ────────────────────────────────────────────────────────────

_TICKER_RE = re.compile(r'^[A-Z]{1,5}(\.[A-Z])?$')

NASDAQ100_FALLBACK = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA", "AVGO", "COST",
    "NFLX", "ASML", "TMUS", "CSCO", "AMD", "ADBE", "PEP", "QCOM", "AZN", "INTU",
    "TXN", "ISRG", "CMCSA", "HON", "AMGN", "AMAT", "BKNG", "VRTX", "MU", "PANW",
    "LRCX", "REGN", "KLAC", "SNPS", "CDNS", "MELI", "CRWD", "ABNB", "MAR", "MDLZ",
    "ORLY", "CTAS", "FTNT", "WDAY", "KDP", "PAYX", "ADP", "ROST", "MNST", "CHTR",
    "FAST", "VRSK", "DXCM", "DLTR", "EA", "BIIB", "IDXX", "ZS", "GEHC", "ON",
    "EXC", "CEG", "ODFL", "CPRT", "CDW", "FANG", "ANSS", "KHC", "SBUX", "PCAR",
    "TTWO", "LULU", "MCHP", "DDOG", "EBAY", "ILMN", "ENPH", "NXPI", "TTD", "PYPL",
    "ADSK", "MRVL", "GILD", "CSX", "ALGN", "CTSH", "PDD", "INTC", "MRNA", "TEAM",
    "ZM", "MTCH", "SPLK", "SIRI", "RIVN", "LCID", "GFS", "WBD", "SMCI", "ARM",
]

# Extra large-cap NASDAQ stocks beyond the NASDAQ-100
NASDAQ200_EXTRA = [
    "PLTR", "COIN", "HOOD", "SHOP", "SPOT", "SNOW", "NET", "OKTA", "HUBS", "TWLO",
    "MDB", "CFLT", "APP", "RBLX", "PINS", "SNAP", "ROKU", "DKNG", "DOCU", "AXON",
    "MSTR", "PAYC", "MANH", "POOL", "GNRC", "TRMB", "NDSN", "WST", "SWKS", "NDAQ",
    "EXAS", "PODD", "BMRN", "EPAM", "FSLR", "RUN", "SEDG", "NIO", "XPEV", "LI",
    "BILI", "JD", "BIDU", "NTES", "GRAB", "SE", "PARA", "NWSA", "FOX", "CHKP",
    "LOGI", "FLEX", "JBHT", "EXPD", "XPO", "SAIA", "CHRW", "IPGP", "ACLS", "ONTO",
    "FORM", "STX", "WDC", "AI", "MPWR", "ENTG", "LYFT", "MNSO", "FUTU", "PSTG",
    "EXPE", "BILL", "SOFI", "AFRM", "UPST", "ZI", "DOCN", "PCOR", "U", "DT",
    "PATH", "GTLB", "ASAN", "MNDY", "TENB", "QLYS", "IOT", "VRNS", "FIVN", "CWAN",
    "NCNO", "FOUR", "BRZE", "NICE", "SMAR", "LSTR", "ESTC", "ZETA", "CSGP", "GRMN",
]


def get_nasdaq100_tickers() -> list[str]:
    """Scrape NASDAQ-100 tickers from Wikipedia, fallback to hardcoded list."""
    try:
        resp = requests.get(
            "https://en.wikipedia.org/wiki/Nasdaq-100",
            headers={"User-Agent": "Mozilla/5.0 (compatible; InvestBot/1.0)"},
            timeout=10,
        )
        soup = BeautifulSoup(resp.content, "lxml")
        table = soup.find("table", {"id": "constituents"})
        if not table:
            print("Wikipedia table not found, using fallback")
            return NASDAQ100_FALLBACK

        tickers = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            # Search all cells for a valid ticker pattern
            for col in cols:
                text = col.text.strip()
                if _TICKER_RE.match(text):
                    tickers.append(text)
                    break

        if len(tickers) < 50:
            print(f"Only {len(tickers)} tickers from Wikipedia, using fallback")
            return NASDAQ100_FALLBACK

        print(f"Got {len(tickers)} tickers from Wikipedia")
        return tickers[:100]
    except Exception as e:
        print(f"Wikipedia scrape failed: {e}, using fallback")
        return NASDAQ100_FALLBACK


def get_nasdaq200_tickers() -> list[str]:
    """Get up to 200 NASDAQ large-cap tickers: scraped NASDAQ-100 + curated extras."""
    scraped = get_nasdaq100_tickers()
    combined = list(dict.fromkeys(scraped + NASDAQ200_EXTRA))
    return combined[:200]


def get_kospi100_tickers() -> list[str]:
    """Fetch KOSPI top-100 by market cap using pykrx. Retries up to 5 trading days back."""
    from pykrx import stock as krx
    dt = datetime.now()
    for _ in range(10):
        while dt.weekday() >= 5:
            dt -= timedelta(days=1)
        date_str = dt.strftime("%Y%m%d")
        try:
            cap_df = krx.get_market_cap_by_ticker(date_str, market="KOSPI")
            if cap_df is not None and not cap_df.empty:
                tickers = cap_df.nlargest(100, "시가총액").index.tolist()
                print(f"Got {len(tickers)} KOSPI tickers (date={date_str})")
                return tickers
        except Exception as e:
            print(f"pykrx error for {date_str}: {e}")
        dt -= timedelta(days=1)
    print("KOSPI 티커를 가져오지 못했습니다 (10일치 재시도 실패)")
    return []


# ── US stock metrics ──────────────────────────────────────────────────────────

def fetch_us_metrics(ticker: str) -> dict | None:
    try:
        t = yf.Ticker(ticker)

        # fast_info: lightweight, reliable price data
        fi = None
        try:
            fi = t.fast_info
        except Exception:
            pass

        # info: fundamentals
        info: dict = {}
        try:
            raw = t.info
            if isinstance(raw, dict) and raw.get("quoteType") not in (None, "NONE"):
                info = raw
        except Exception:
            pass

        # Current price — fast_info is more reliable in yfinance 1.x
        current_price = _fi_attr(fi, "last_price") or _fi_attr(fi, "previous_close")
        if not current_price:
            current_price = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("previousClose")
            )

        # Market cap
        market_cap = _fi_attr(fi, "market_cap") or info.get("marketCap")

        # 52-week range
        w52_high = _fi_attr(fi, "fifty_two_week_high") or info.get("fiftyTwoWeekHigh")
        w52_low = _fi_attr(fi, "fifty_two_week_low") or info.get("fiftyTwoWeekLow")

        name = info.get("longName") or info.get("shortName") or ticker

        if not name or name == ticker:
            return None  # likely invalid ticker

        return {
            "name": name,
            "sector": info.get("sector") or "Unknown",
            "industry": info.get("industry") or "Unknown",
            "market_cap": market_cap,
            "current_price": current_price,
            "pe_ratio": _pos(info.get("trailingPE")),
            "forward_pe": _pos(info.get("forwardPE")),
            "pb_ratio": _pos(info.get("priceToBook")),
            "ev_ebitda": _pos(info.get("enterpriseToEbitda")),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "operating_margin": info.get("operatingMargins"),
            "profit_margin": info.get("profitMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "free_cashflow": info.get("freeCashflow"),
            "dividend_yield": info.get("dividendYield"),
            "week52_high": w52_high,
            "week52_low": w52_low,
            "beta": info.get("beta"),
            "target_mean_price": info.get("targetMeanPrice"),
            "analyst_count": int(info.get("numberOfAnalystOpinions") or 0),
            "price_to_sales": _pos(info.get("priceToSalesTrailing12Months")),
        }
    except Exception as e:
        print(f"  [ERR] {ticker}: {e}")
        return None


# ── KR stock metrics ──────────────────────────────────────────────────────────

def fetch_kr_metrics(krx_ticker: str) -> dict | None:
    try:
        from pykrx import stock as krx
        date_str = _last_trading_day()

        name = krx.get_market_ticker_name(krx_ticker)
        if not name:
            return None

        fund = krx.get_market_fundamental_by_ticker(date_str, market="KOSPI")
        if krx_ticker not in fund.index:
            return None
        f = fund.loc[krx_ticker]

        cap = krx.get_market_cap_by_ticker(date_str, market="KOSPI")
        market_cap = int(cap.loc[krx_ticker, "시가총액"]) if krx_ticker in cap.index else None

        ohlcv = krx.get_market_ohlcv_by_date(
            (datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
            date_str, krx_ticker,
        )
        current_price = float(ohlcv["종가"].iloc[-1]) if not ohlcv.empty else None

        # Sector from yfinance .KS
        sector = "Unknown"
        try:
            yfinfo = yf.Ticker(f"{krx_ticker}.KS").info
            sector = yfinfo.get("sector") or "Unknown"
        except Exception:
            pass

        pe = float(f.get("PER") or 0)
        pb = float(f.get("PBR") or 0)
        div = float(f.get("DIV") or 0)

        return {
            "name": name,
            "sector": sector,
            "industry": "Unknown",
            "market_cap": market_cap,
            "current_price": current_price,
            "pe_ratio": pe if pe > 0 else None,
            "pb_ratio": pb if pb > 0 else None,
            "ev_ebitda": None,
            "roe": None,
            "roa": None,
            "operating_margin": None,
            "profit_margin": None,
            "revenue_growth": None,
            "earnings_growth": None,
            "debt_to_equity": None,
            "current_ratio": None,
            "free_cashflow": None,
            "dividend_yield": div / 100 if div > 0 else None,
            "week52_high": None,
            "week52_low": None,
            "beta": None,
        }
    except Exception as e:
        print(f"  [ERR KRX] {krx_ticker}: {e}")
        return None


# ── Price history ─────────────────────────────────────────────────────────────

PERIOD_MAP = {
    "1w": "5d",
    "1m": "1mo",
    "3m": "3mo",
    "6m": "6mo",
    "1y": "1y",
    "3y": "3y",
}


def fetch_price_history(ticker: str, market: str, period: str = "1y") -> list[dict]:
    """Fetch OHLCV history. Ticker format: AAPL (nasdaq) or KS005930 (kospi)."""
    if market == "kospi":
        krx_code = ticker.replace("KS", "", 1)
        yf_ticker = f"{krx_code}.KS"
    else:
        yf_ticker = ticker

    yf_period = PERIOD_MAP.get(period, "1y")
    try:
        hist = yf.Ticker(yf_ticker).history(period=yf_period)
        if hist.empty:
            return []

        # Normalize column names (handle both capitalised and lowercase)
        col = {c.lower(): c for c in hist.columns}
        c_open  = col.get("open", "Open")
        c_high  = col.get("high", "High")
        c_low   = col.get("low", "Low")
        c_close = col.get("close", "Close")
        c_vol   = col.get("volume", "Volume")

        rows = []
        for date, row in hist.iterrows():
            close = row.get(c_close)
            try:
                close_f = float(close)
            except (TypeError, ValueError):
                continue
            if math.isnan(close_f) or close_f <= 0:
                continue

            def _safe(v, fallback):
                try:
                    f = float(v)
                    return round(f if not math.isnan(f) else fallback, 4)
                except (TypeError, ValueError):
                    return round(fallback, 4)

            rows.append({
                "date":   str(date.date()),
                "open":   _safe(row.get(c_open),  close_f),
                "high":   _safe(row.get(c_high),  close_f),
                "low":    _safe(row.get(c_low),   close_f),
                "close":  round(close_f, 4),
                "volume": int(row.get(c_vol, 0) or 0),
            })
        return rows
    except Exception as e:
        print(f"  [ERR history] {ticker}: {e}")
        return []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pos(val):
    return val if (val is not None and val > 0) else None


def _fi_attr(fi, name: str):
    """Safely get attribute from fast_info."""
    if fi is None:
        return None
    try:
        v = getattr(fi, name, None)
        return v if v and v > 0 else None
    except Exception:
        return None


def _last_trading_day() -> str:
    """Return last weekday as YYYYMMDD (for pykrx)."""
    dt = datetime.now()
    while dt.weekday() >= 5:  # Saturday=5, Sunday=6
        dt -= timedelta(days=1)
    return dt.strftime("%Y%m%d")


# ── Financial statement data (for Fundamental module) ─────────────────────────

def fetch_financial_data(ticker: str, market_cap: float | None) -> dict:
    """
    Fetch 3-year income statement, cash flow, and balance sheet via yfinance.
    Returns a dict consumed by scorer.score_fundamental().

    New fields vs old version:
      - ar_growth, inv_growth : AR/inventory YoY growth from balance sheet
      - buyback_yield          : share repurchase / market_cap
      (net_cash_ratio removed; current_ratio comes from metrics dict)
    """
    result: dict = {
        "op_income_3y": [], "op_cf_3y": [], "net_income_3y": [],
        "capex_3y": [], "fcf_3y": [], "fcf_yields_3y": [],
        "current_fcf_yield": None, "accruals_ok": None,
        "ar_growth": None, "inv_growth": None, "buyback_yield": None,
        "revenue_3y": [], "revenue_cagr": None, "rd_ratio": None,
    }
    try:
        t = yf.Ticker(ticker)

        # ── Income Statement ──────────────────────────────────────────────────
        fins = None
        try:
            fins = t.financials
            if fins is not None and not fins.empty:
                for col in list(fins.columns)[:3]:
                    oi = _row(fins[col], [
                        "Operating Income", "EBIT", "Operating Profit",
                        "Total Operating Income As Reported",
                    ])
                    ni = _row(fins[col], [
                        "Net Income", "Net Income Common Stockholders",
                        "Net Income From Continuing Operation Net Minority Interest",
                    ])
                    rev = _row(fins[col], [
                        "Total Revenue", "Revenue", "Net Revenue", "Total Revenues",
                    ])
                    rd = _row(fins[col], [
                        "Research And Development",
                        "Research Development",
                        "Research & Development",
                        "Research And Development Expense",
                        "Research Development Expense",
                        "Research And Development Expenses",
                        "Total Research And Development",
                    ])
                    if oi is not None:
                        result["op_income_3y"].append(float(oi))
                    if ni is not None:
                        result["net_income_3y"].append(float(ni))
                    if rev is not None:
                        try:
                            v = float(rev)
                            if not math.isnan(v) and v > 0:
                                result["revenue_3y"].append(v)
                        except (TypeError, ValueError):
                            pass
                    if rd is not None:
                        try:
                            v = abs(float(rd))
                            if not math.isnan(v) and v > 0:
                                result.setdefault("_rd_3y", []).append(v)
                        except (TypeError, ValueError):
                            pass

                # Revenue CAGR from 3-year data
                rev3 = result["revenue_3y"]
                if len(rev3) >= 2 and rev3[-1] > 0:
                    n = len(rev3) - 1
                    result["revenue_cagr"]      = (rev3[0] / rev3[-1]) ** (1.0 / n) - 1
                    result["rev_cagr_years"]    = n  # scorer uses this to flag YoY fallback

                # R&D ratio vs most recent revenue
                rd3 = result.pop("_rd_3y", [])
                if rd3 and rev3 and rev3[0] > 0:
                    result["rd_ratio"] = rd3[0] / rev3[0]
        except Exception:
            pass

        # ── Cash Flow Statement ───────────────────────────────────────────────
        cf = None
        try:
            cf = t.cashflow
            if cf is not None and not cf.empty:
                for col in list(cf.columns)[:3]:
                    ocf = _row(cf[col], [
                        "Operating Cash Flow", "Total Cash From Operating Activities",
                        "Cash From Operations", "Net Cash Provided By Operating Activities",
                    ])
                    capex = _row(cf[col], [
                        "Capital Expenditure",
                        "Capital Expenditures",
                        "Capital Expenditure Reported",
                        "Capital Expenditures Reported",
                        "Purchase Of Plant Property And Equipment",
                        "Purchase Of Property Plant And Equipment",
                        "Purchases Of Property Plant And Equipment",
                        "Purchase Of Ppe",
                        "Net Ppe Purchase And Sale",
                    ])
                    if ocf is not None:
                        result["op_cf_3y"].append(float(ocf))
                    if capex is not None:
                        result["capex_3y"].append(abs(float(capex)))

                # Buyback yield — most recent year only
                col0 = list(cf.columns)[0]
                buyback = _row(cf[col0], [
                    "Repurchase Of Capital Stock",
                    "Common Stock Repurchased",
                    "Repurchase Of Common Stock",
                    "Purchase Of Common Stock",
                ])
                if buyback is not None and market_cap and market_cap > 0:
                    result["buyback_yield"] = abs(float(buyback)) / market_cap
        except Exception:
            pass

        # ── FCF & Accruals ────────────────────────────────────────────────────
        n = min(len(result["op_cf_3y"]), len(result["capex_3y"]))
        for i in range(n):
            fcf = result["op_cf_3y"][i] - result["capex_3y"][i]
            result["fcf_3y"].append(fcf)
            if market_cap and market_cap > 0:
                result["fcf_yields_3y"].append(fcf / market_cap)

        if result["fcf_yields_3y"]:
            result["current_fcf_yield"] = result["fcf_yields_3y"][0]

        if result["net_income_3y"] and result["op_cf_3y"]:
            result["accruals_ok"] = result["net_income_3y"][0] < result["op_cf_3y"][0]

        # ── Balance Sheet: AR & Inventory growth ─────────────────────────────
        try:
            bs = t.balance_sheet
            if bs is not None and not bs.empty and len(bs.columns) >= 2:
                col0, col1 = list(bs.columns)[0], list(bs.columns)[1]

                # Accounts Receivable
                ar_cur  = _row(bs[col0], ["Accounts Receivable", "Net Receivables", "Receivables"])
                ar_prev = _row(bs[col1], ["Accounts Receivable", "Net Receivables", "Receivables"])
                if ar_cur is not None and ar_prev is not None and float(ar_prev) != 0:
                    result["ar_growth"] = (float(ar_cur) - float(ar_prev)) / abs(float(ar_prev))

                # Inventory
                inv_cur  = _row(bs[col0], ["Inventory", "Inventories", "Finished Goods"])
                inv_prev = _row(bs[col1], ["Inventory", "Inventories", "Finished Goods"])
                if inv_cur is not None and inv_prev is not None and float(inv_prev) != 0:
                    result["inv_growth"] = (float(inv_cur) - float(inv_prev)) / abs(float(inv_prev))
        except Exception:
            pass

    except Exception as e:
        print(f"  [ERR financial] {ticker}: {e}")

    return result


def fetch_benchmark_history(period: str = "1y") -> list[dict]:
    """Fetch NASDAQ composite (^IXIC) price history for RS calculation."""
    return fetch_price_history("^IXIC", "nasdaq", period)


def _row(series, keys: list[str]):
    """Get first matching key from a pandas Series, case-insensitive. Returns None if missing/NaN."""
    idx_lower = {str(k).lower(): k for k in series.index}
    for key in keys:
        real = idx_lower.get(key.lower())
        if real is not None:
            try:
                val = series[real]
                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                    return val
            except Exception:
                pass
    return None
