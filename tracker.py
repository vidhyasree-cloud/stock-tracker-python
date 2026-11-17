"""Stock Tracker - Step 1 (Python, no API key needed)
Live prices + history from Yahoo Finance chart API (public, free).
Simple trend forecast = last price + recent daily trend, labelled as a
learning model, NOT financial advice. No real money, no trading.

Run:  python tracker.py
Then type a ticker, e.g. AAPL
"""
import json, os, statistics
from datetime import datetime

try:
    import httpx
except ImportError:
    httpx = None

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "portfolio.json")

def _client():
    # Same proxy pattern as the MCP servers: works in this VM and on a PC.
    import ssl
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    ctx = ssl.create_default_context()
    if os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
        ctx.load_verify_locations("/etc/ssl/certs/ca-certificates.crt")
    return httpx.Client(proxy=proxy or None, trust_env=False, verify=ctx,
                        headers={"User-Agent": "stock-tracker-python/1.0"},
                        timeout=20)

def get_history(ticker, days=90):
    """Return (current_price, [closes]) from Yahoo chart API."""
    ticker = ticker.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"range": f"{days}d", "interval": "1d"}
    with _client() as c:
        r = c.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    result = data["chart"]["result"][0]
    meta = result["meta"]
    closes = [x for x in result["indicators"]["quote"][0]["close"] if x is not None]
    if not closes:
        raise ValueError(f"No price data for {ticker}")
    return meta["regularMarketPrice"], closes, meta.get("longName", ticker)

def simple_forecast(closes, days_ahead=30):
    """Simple trend forecast: average daily change over last 30 days,
    projected forward. Returns (target, low, high, direction)."""
    recent = closes[-30:] if len(closes) >= 30 else closes
    changes = [recent[i+1]-recent[i] for i in range(len(recent)-1)]
    avg_change = statistics.mean(changes) if changes else 0.0
    vol = statistics.pstdev(changes) if len(changes) > 1 else 0.0
    last = closes[-1]
    target = last + avg_change * days_ahead
    low = target - vol * (days_ahead ** 0.5)
    high = target + vol * (days_ahead ** 0.5)
    direction = "up" if target > last else "down" if target < last else "flat"
    return target, low, high, direction

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    return {}  # {TICKER: {"shares": n, "buy_price": p}}

def save_portfolio(p):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(p, f, indent=2)

def show_portfolio():
    p = load_portfolio()
    if not p:
        print("\nPortfolio is empty. Add a holding first (option 1).")
        return
    print("\n--- Your portfolio (live prices) ---")
    total_value = total_cost = 0.0
    for ticker, h in p.items():
        try:
            price, closes, name = get_history(ticker, days=30)
        except Exception as e:
            print(f"{ticker}: could not fetch price ({e})")
            continue
        value = price * h["shares"]
        cost = h["buy_price"] * h["shares"]
        gain = value - cost
        total_value += value; total_cost += cost
        target, low, high, direction = simple_forecast(closes, 30)
        print(f"{ticker} {name}: {h['shares']} shares @ ${price:.2f} = ${value:,.2f} "
              f"(paid ${cost:,.2f}, gain ${gain:+,.2f})")
        print(f"   30-day trend forecast: ${target:.2f} (range ${low:.2f}-${high:.2f}, {direction}) - learning model only, not advice")
    print(f"\nTOTAL value: ${total_value:,.2f} | paid: ${total_cost:,.2f} | gain: ${total_value-total_cost:+,.2f}")

def main():
    if httpx is None:
        print("Install httpx first:  pip install httpx")
        return
    while True:
        print("\n=== Stock Tracker (Step 1) ===")
        print("1. Add a holding   2. Show portfolio   3. Look up one stock   4. Quit")
        choice = input("Pick 1-4: ").strip()
        if choice == "1":
            t = input("Ticker (e.g. AAPL): ").strip().upper()
            try:
                price, closes, name = get_history(t, days=30)
                print(f"{t} {name}: live price ${price:.2f}")
            except Exception as e:
                print(f"Could not find {t}: {e}")
                continue
            shares = float(input("How many shares? "))
            buy = float(input("What price did you pay per share? "))
            p = load_portfolio(); p[t] = {"shares": shares, "buy_price": buy}
            save_portfolio(p)
            print(f"Saved {shares} x {t} @ ${buy:.2f}")
        elif choice == "2":
            show_portfolio()
        elif choice == "3":
            t = input("Ticker: ").strip().upper()
            try:
                price, closes, name = get_history(t, days=90)
                target, low, high, direction = simple_forecast(closes, 30)
                print(f"\n{t} {name}: ${price:.2f}  (90 days of closes: {len(closes)})")
                print(f"30-day trend forecast: ${target:.2f}, range ${low:.2f}-${high:.2f}, {direction}")
                print("Learning model only - not financial advice.")
            except Exception as e:
                print(f"Could not fetch {t}: {e}")
        elif choice == "4":
            print("Bye!")
            break
        else:
            print("Pick 1, 2, 3 or 4.")

if __name__ == "__main__":
    main()
