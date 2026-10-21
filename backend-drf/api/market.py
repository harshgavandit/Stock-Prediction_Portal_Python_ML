"""Yahoo Finance market data with bounded requests and per-process caching."""
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import quote

import numpy as np
import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MarketDataError(Exception):
    pass


def history(ticker, period="10y"):
    key = f"history:{ticker}:{period}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            response = requests.get(
                f"https://{host}/v8/finance/chart/{quote(ticker, safe='')}",
                params={"range": period, "interval": "1d"},
                headers={"User-Agent": "Mozilla/5.0"}, timeout=8,
            )
            response.raise_for_status()
            result = response.json()["chart"]["result"][0]
            closes = result["indicators"]["quote"][0]["close"]
            points = [(stamp, float(close)) for stamp, close in zip(result["timestamp"], closes)
                      if close is not None and np.isfinite(close) and close > 0]
            if not points:
                continue
            value = {"dates": [datetime.fromtimestamp(t, timezone.utc).date().isoformat() for t, _ in points],
                     "close": [p for _, p in points], "meta": result["meta"], "source": "Yahoo Finance"}
            cache.set(key, value, 900 if period == "10y" else 60)
            return value
        except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
            continue
    # yfinance can recover when Yahoo requires its cookie/crumb handshake.
    try:
        import yfinance as yf
        frame = yf.Ticker(ticker).history(period=period, auto_adjust=False, timeout=8, raise_errors=True)
        frame = frame.loc[frame["Close"].notna() & (frame["Close"] > 0)]
        if not frame.empty:
            value = {"dates": [d.date().isoformat() for d in frame.index],
                     "close": frame["Close"].astype(float).tolist(),
                     "meta": {"currency": "INR" if ticker.endswith((".NS", ".BO")) else None},
                     "source": "Yahoo Finance via yfinance"}
            cache.set(key, value, 900 if period == "10y" else 60)
            return value
    except Exception:
        logger.warning("Market provider could not serve %s", ticker)
    raise MarketDataError("Market data is unavailable for this symbol. Check the ticker or try again shortly.")


def quote_price(ticker):
    try:
        data = history(ticker, "5d")
        closes, meta = data["close"], data["meta"]
        price = float(meta.get("regularMarketPrice") or closes[-1])
        previous = float(meta.get("chartPreviousClose") or closes[-2]) if len(closes) > 1 else closes[-1]
        # chartPreviousClose covers the entire range; the prior daily close is the proper daily baseline.
        if len(closes) > 1:
            previous = closes[-2]
        change = price - previous
        return ticker, {
            "price": round(price, 2), "change": round(change, 2),
            "percent_change": round(100 * change / previous, 2) if previous else 0,
            "currency": meta.get("currency"),
            "as_of": datetime.fromtimestamp(meta["regularMarketTime"], timezone.utc).isoformat()
                     if meta.get("regularMarketTime") else data["dates"][-1],
            "source": data["source"],
        }
    except MarketDataError as exc:
        return ticker, {"price": None, "change": None, "percent_change": None, "error": str(exc)}


def prices(tickers):
    with ThreadPoolExecutor(max_workers=5) as executor:
        return dict(executor.map(quote_price, tickers))
