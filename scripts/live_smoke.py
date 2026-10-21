"""Exercise the deployed app with synthetic account data and real market requests.

Usage: python scripts/live_smoke.py https://stock-prediction-portal-kohl.vercel.app
Credentials and full chart responses stay in ignored .tmp/, never in reports.
"""
import base64
import json
import math
import secrets
import sys
import time
import uuid
from pathlib import Path

import requests

root = Path(__file__).resolve().parent.parent
temporary = root / ".tmp"
temporary.mkdir(exist_ok=True)
base = sys.argv[1].rstrip("/")
session = requests.Session()
report = {"url": base, "checks": [], "predictions": {}, "quotes": {}}


def check(condition, description):
    if not condition:
        raise RuntimeError(description)
    report["checks"].append(description)
    print("PASS:", description, flush=True)


def request(method, path, expected=200, **kwargs):
    response = session.request(method, base + "/api/v1/" + path, timeout=65, **kwargs)
    check(response.status_code == expected, f"{method} {path}: expected HTTP {expected}, got {response.status_code}")
    return response.json()


check(request("GET", "health/")["status"] == "ok", "Database and model ready")
for route in ("/", "/login", "/register", "/dashboard", "/profile"):
    response = requests.get(base + route, timeout=30)
    check(response.status_code == 200 and '<div id="root">' in response.text, f"SPA direct route {route}")
request("GET", "profile/", expected=401)
username = "verify_" + uuid.uuid4().hex[:12]
password = secrets.token_urlsafe(24)
account = {"username": username, "password": password, "email": username + "@example.invalid"}
(temporary / "live-smoke-account.json").write_text(json.dumps(account))
request("POST", "register/", expected=201, json=account)
tokens = request("POST", "token/", json={"username": username, "password": password})
session.headers["Authorization"] = "Bearer " + tokens["access"]
check(request("GET", "protected-view/")["user"]["username"] == username, "Authenticated identity")
request("PATCH", "profile/", json={"email": "verified-" + username + "@example.invalid"})
request("GET", "portfolio/")
request("POST", "portfolio/", json={"tickers": ["AAPL", "RELIANCE.NS"]})
check(request("GET", "portfolio/")["tickers"] == ["AAPL", "RELIANCE.NS"], "Saved watchlist")
request("POST", "portfolio/", json={"tickers": []})
check(request("GET", "portfolio/")["tickers"] == [], "Empty watchlist remains saved")
request("POST", "portfolio/", json={"tickers": ["AAPL", "RELIANCE.NS"]})
request("POST", "portfolio/", expected=400, json={"tickers": ["AAPL"] * 11})
request("POST", "predict/", expected=400, json={"ticker": "../bad"})
refreshed = request("POST", "token/refresh/", json={"refresh": tokens["refresh"]})
session.headers["Authorization"] = "Bearer " + refreshed["access"]
quotes = request("POST", "live-prices/", json={"tickers": ["AAPL", "RELIANCE.NS", "TCS.NS", "INFY.NS"]})["prices"]
for symbol, quote in quotes.items():
    check(isinstance(quote.get("price"), (int, float)) and quote["price"] > 0, f"Real market quote: {symbol}")
    report["quotes"][symbol] = quote
for symbol in ("AAPL", "RELIANCE.NS"):
    started = time.monotonic()
    result = request("POST", "predict/", json={"ticker": symbol})
    check(result["history_rows"] > 1000 and math.isfinite(result["next_close"]), f"Real historical inference: {symbol}")
    for name in ("plot_img", "plot_100_dma", "plot_200_dma", "plot_prediction"):
        encoded = result[name].split(",", 1)[1]
        check(base64.b64decode(encoded).startswith(b"\x89PNG"), f"Renderable PNG: {symbol} {name}")
    check(all(math.isfinite(result[name]) for name in ("mse", "rmse", "r2")), f"Finite evaluation metrics: {symbol}")
    report["predictions"][symbol] = {key: result[key] for key in ("as_of", "history_rows", "evaluation_rows", "mse", "rmse", "r2", "next_close", "currency", "source")}
    report["predictions"][symbol]["seconds"] = round(time.monotonic() - started, 2)
    (temporary / f"{symbol}-response.json").write_text(json.dumps(result))
# An independent HTTP session must see the same database state.
session = requests.Session()
tokens = request("POST", "token/", json={"username": username, "password": password})
session.headers["Authorization"] = "Bearer " + tokens["access"]
check(request("GET", "portfolio/")["tickers"] == ["AAPL", "RELIANCE.NS"], "Watchlist persists across fresh login")
(temporary / "live-verification.json").write_text(json.dumps(report, indent=2))
print(json.dumps({"passed": len(report["checks"]), "predictions": report["predictions"]}, indent=2))
