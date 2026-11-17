"""Stock Tracker - Step 3: web dashboard (FastAPI)
Reuses tracker.py: live prices from Yahoo, portfolio.json, simple forecast.
Run:  uvicorn app:app --reload
Then open:  http://127.0.0.1:8000
Test data only - no real money, no trading. Forecast is a learning model.
"""
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import tracker

app = FastAPI(title="Stock Tracker")

def portfolio_rows():
    rows, total_value, total_cost = [], 0.0, 0.0
    for ticker, h in tracker.load_portfolio().items():
        try:
            price, closes, name = tracker.get_history(ticker, days=90)
        except Exception as e:
            rows.append({"ticker": ticker, "name": "?", "error": str(e), **h})
            continue
        value = price * h["shares"]; cost = h["buy_price"] * h["shares"]
        target, low, high, direction = tracker.simple_forecast(closes, 30)
        total_value += value; total_cost += cost
        rows.append({"ticker": ticker, "name": name, "price": price,
                     "shares": h["shares"], "buy": h["buy_price"],
                     "value": value, "gain": value - cost,
                     "target": target, "low": low, "high": high,
                     "direction": direction})
    return rows, total_value, total_cost

def page(rows, total_value, total_cost):
    cards = ""
    for r in rows:
        if "error" in r:
            cards += f"<div class='card'><b>{r['ticker']}</b> — could not fetch price</div>"
            continue
        gain_cls = "up" if r["gain"] >= 0 else "down"
        cards += f"""<div class='card'>
          <b>{r['ticker']}</b> {r['name']}<br>
          Price ${r['price']:.2f} · {r['shares']} shares · Value <b>${r['value']:,.2f}</b><br>
          Paid ${r['buy']:.2f} · Gain <span class='{gain_cls}'>${r['gain']:+,.2f}</span><br>
          30-day forecast: ${r['target']:.2f} (${r['low']:.2f}–${r['high']:.2f}, {r['direction']})
        </div>"""
    gain = total_value - total_cost
    return f"""<!doctype html><html><head><meta charset='utf-8'>
    <title>Stock Tracker</title>
    <style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px}}
    .total{{font-size:28px}} .up{{color:green}} .down{{color:red}}
    .card{{border:1px solid #ccc;border-radius:10px;padding:14px;margin:12px 0}}
    input,button{{padding:8px;margin:4px 2px}}</style></head><body>
    <h1>📈 Stock Tracker</h1>
    <p class='total'>Total value: <b>${total_value:,.2f}</b> · Gain: <b>${gain:+,.2f}</b></p>
    <p>Test data only — no real money, no trading. Forecast is a learning model, not advice.</p>
    {cards or "<p>No holdings yet — add one below.</p>"}
    <h2>Add a holding</h2>
    <form method='post' action='/add'>
      <input name='ticker' placeholder='Ticker, e.g. AAPL' required>
      <input name='shares' type='number' step='any' placeholder='Shares' required>
      <input name='buy_price' type='number' step='any' placeholder='Price paid' required>
      <button>Add</button>
    </form>
    <h2>Look up one stock</h2>
    <form method='get' action='/lookup'>
      <input name='ticker' placeholder='Ticker, e.g. MSFT' required>
      <button>Look up</button>
    </form>
    <p><a href='/'>Refresh prices</a></p>
    </body></html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    rows, tv, tc = portfolio_rows()
    return page(rows, tv, tc)

@app.post("/add")
def add(ticker: str = Form(...), shares: float = Form(...), buy_price: float = Form(...)):
    t = ticker.strip().upper()
    price, _, name = tracker.get_history(t, days=30)  # validates the ticker
    p = tracker.load_portfolio(); p[t] = {"shares": shares, "buy_price": buy_price}
    tracker.save_portfolio(p)
    return RedirectResponse("/", status_code=303)

@app.get("/lookup", response_class=HTMLResponse)
def lookup(ticker: str):
    t = ticker.strip().upper()
    price, closes, name = tracker.get_history(t, days=90)
    target, low, high, direction = tracker.simple_forecast(closes, 30)
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>{t}</title>
    <style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px}}</style></head><body>
    <h1>{t} — {name}</h1><p>Live price: <b>${price:.2f}</b></p>
    <p>30-day trend forecast: <b>${target:.2f}</b> (range ${low:.2f}–${high:.2f}, {direction})</p>
    <p>Learning model only — not financial advice.</p><p><a href='/'>← Back to dashboard</a></p></body></html>"""
