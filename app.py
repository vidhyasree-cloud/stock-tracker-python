"""Stock Tracker - Step 3: web dashboard (FastAPI)
Reuses tracker.py: live prices from Yahoo, portfolio.json, simple forecast.
Run:  uvicorn app:app --reload
Then open:  http://127.0.0.1:8000  (user view) and http://127.0.0.1:8000/admin  (admin view)
Test data only - no real money, no trading. Forecast is a learning model.
"""
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import hashlib, os
import tracker

app = FastAPI(title="Stock Tracker")

def admin_password():
    """The one admin password, read fresh on every request.
    1) ADMIN_PASSWORD env var if set, else
    2) admin_password.txt next to app.py (one line, your password only).
    That file is gitignored — it never goes to GitHub, and it works in any
    PowerShell window, so there is no 'wrong window' mismatch."""
    env_pw = os.environ.get("ADMIN_PASSWORD", "").strip()
    if env_pw:
        return env_pw
    try:
        with open(os.path.join(os.path.dirname(__file__), "admin_password.txt")) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def _auth_token(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def is_admin(request: Request):
    pw = admin_password()
    return bool(pw) and request.cookies.get("admin_auth") == _auth_token(pw)

def login_page(message=""):
    return f"""<!doctype html><html><head><meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>Admin login — Stock Tracker</title><style>{STYLE}</style></head><body><div class='wrap'>
    <header><h1>🛠️ Admin View</h1><p>Enter the admin password to see the full view</p></header>
    <nav><a href='/'>User view</a><a href='/admin' class='active'>Admin view</a></nav>
    <section><h2>Admin password</h2>
    <p style='color:#f87171'>{message}</p>
    <form method='post' action='/admin/login'>
      <input name='password' type='password' placeholder='Admin password' required>
      <button>Unlock admin</button>
    </form></section>
    <p class='note'>The password lives only on this computer — in admin_password.txt or ADMIN_PASSWORD. It is not in the code or on GitHub.</p>
    </div></body></html>"""

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

STYLE = """
    *{box-sizing:border-box} body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;
    margin:0;background:#0f172a;color:#e2e8f0;min-height:100vh}
    .wrap{max-width:760px;margin:0 auto;padding:32px 20px 48px}
    header{background:linear-gradient(135deg,#4f46e5,#06b6d4);border-radius:20px;padding:28px;
    box-shadow:0 12px 32px rgba(79,70,229,.35)}
    header h1{margin:0;font-size:30px} header p{margin:6px 0 0;opacity:.85}
    .total-card{background:#1e293b;border:1px solid #334155;border-radius:20px;padding:24px;
    margin:20px 0;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
    .total-card .label{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8}
    .total-card .big{font-size:34px;font-weight:800;margin-top:4px}
    .up{color:#4ade80} .down{color:#f87171}
    .pill{display:inline-block;padding:3px 10px;border-radius:999px;font-size:13px;font-weight:700;
    background:rgba(74,222,128,.15);color:#4ade80}
    .pill.down{background:rgba(248,113,113,.15);color:#f87171}
    .card{background:#1e293b;border:1px solid #334155;border-radius:16px;padding:18px 20px;margin:14px 0}
    .card .head{display:flex;justify-content:space-between;align-items:baseline}
    .card .ticker{font-size:20px;font-weight:800} .card .name{color:#94a3b8}
    .card .value{font-size:24px;font-weight:800;margin-top:8px}
    .card .meta{color:#cbd5e1;line-height:1.7}
    .forecast{margin-top:10px;padding:10px 12px;border-radius:10px;background:#0f172a;color:#a5f3fc}
    section{background:#1e293b;border:1px solid #334155;border-radius:16px;padding:20px;margin-top:20px}
    section h2{margin:0 0 12px;font-size:18px}
    input{padding:11px 12px;border-radius:10px;border:1px solid #475569;background:#0f172a;
    color:#e2e8f0;margin:4px 4px 4px 0} button{padding:11px 18px;border-radius:10px;border:0;
    background:linear-gradient(135deg,#4f46e5,#06b6d4);color:#fff;font-weight:700;cursor:pointer}
    a{color:#67e8f9} .note{color:#94a3b8;font-size:14px}
    nav{display:flex;gap:8px;margin:16px 0}
    nav a{padding:8px 14px;border-radius:999px;background:#1e293b;border:1px solid #334155;
    color:#e2e8f0;text-decoration:none;font-weight:600}
    nav a.active{background:linear-gradient(135deg,#4f46e5,#06b6d4);border-color:transparent;color:#fff}
    table{width:100%;border-collapse:collapse;background:#1e293b;border-radius:16px;overflow:hidden}
    th,td{padding:12px 10px;text-align:left;border-bottom:1px solid #334155;font-size:14px}
    th{color:#94a3b8;text-transform:uppercase;font-size:12px;letter-spacing:.06em}
    tr:last-child td{border-bottom:0} tfoot td{font-weight:800;background:#0f172a}
    .danger{background:#dc2626 !important}
    """

def admin_page(rows, total_value, total_cost):
    body = ""
    for r in rows:
        if "error" in r:
            body += f"<tr><td>{r['ticker']}</td><td colspan='7'>could not fetch price</td></tr>"
            continue
        gain_cls = "up" if r["gain"] >= 0 else "down"
        body += f"""<tr><td><b>{r['ticker']}</b><br><span class='note'>{r['name']}</span></td>
        <td>{r['shares']}</td><td>${r['buy']:.2f}</td><td>${r['price']:.2f}</td>
        <td>${r['buy'] * r['shares']:,.2f}</td><td>${r['value']:,.2f}</td>
        <td class='{gain_cls}'>${r['gain']:+,.2f}</td>
        <td>${r['target']:.2f} ({r['direction']})</td>
        <td><form method='post' action='/remove' style='margin:0'>
        <input type='hidden' name='ticker' value='{r['ticker']}'><button class='danger'>Remove</button></form></td></tr>"""
    gain = total_value - total_cost
    total_shares = sum(r.get("shares", 0) for r in rows)
    return f"""<!doctype html><html><head><meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>Admin — Stock Tracker</title><style>{STYLE}</style></head><body><div class='wrap' style='max-width:960px'>
    <header><h1>🛠️ Admin View</h1><p>Full view — every share purchased, live prices, totals</p></header>
    <nav><a href='/'>User view</a><a href='/admin' class='active'>Admin view</a></nav>
    <div class='total-card'>
      <div><div class='label'>Holdings</div><div class='big'>{len(rows)}</div></div>
      <div><div class='label'>Total shares</div><div class='big'>{total_shares:g}</div></div>
      <div><div class='label'>Total paid</div><div class='big'>${total_cost:,.2f}</div></div>
      <div><div class='label'>Total value</div><div class='big'>${total_value:,.2f}</div></div>
      <div><div class='label'>All-time gain</div><div class='big {"up" if gain >= 0 else "down"}'>${gain:+,.2f}</div></div>
    </div>
    <table><thead><tr><th>Stock</th><th>Shares</th><th>Buy price</th><th>Live price</th>
    <th>Paid</th><th>Value</th><th>Gain</th><th>30-day forecast</th><th></th></tr></thead>
    <tbody>{body or "<tr><td colspan='9'>No holdings yet.</td></tr>"}</tbody>
    <tfoot><tr><td>Total</td><td>{total_shares:g}</td><td></td><td></td>
    <td>${total_cost:,.2f}</td><td>${total_value:,.2f}</td><td>${gain:+,.2f}</td><td></td><td></td></tr></tfoot></table>
    <p class='note'>Test data only — no real money, no trading. Forecast is a learning model, not advice.</p>
    <p><a href='/admin'>↻ Refresh prices</a> · <a href='/admin/logout'>Log out of admin</a></p>
    </div></body></html>"""

def page(rows, total_value, total_cost):
    cards = ""
    for r in rows:
        if "error" in r:
            cards += f"<div class='card'><b>{r['ticker']}</b> — could not fetch price</div>"
            continue
        gain_cls = "up" if r["gain"] >= 0 else "down"
        dir_cls = "" if r["direction"] == "up" else "down"
        cards += f"""<div class='card'>
          <div class='head'><span><span class='ticker'>{r['ticker']}</span>
          <span class='name'>{r['name']}</span></span>
          <span class='pill {dir_cls}'>▲ {r['direction']}</span></div>
          <div class='value'>${r['value']:,.2f}</div>
          <div class='meta'>Price ${r['price']:.2f} · {r['shares']} shares ·
          Paid ${r['buy']:.2f} · Gain <span class='{gain_cls}'>${r['gain']:+,.2f}</span></div>
          <div class='forecast'>30-day forecast: <b>${r['target']:.2f}</b>
          (${r['low']:.2f} – ${r['high']:.2f})</div>
        </div>"""
    gain = total_value - total_cost
    gain_cls = "up" if gain >= 0 else "down"
    return f"""<!doctype html><html><head><meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>Stock Tracker</title><style>{STYLE}</style></head><body><div class='wrap'>
    <header><h1>📈 Stock Tracker</h1><p>Live prices · portfolio value · AI-style trend forecast</p></header>
    <nav><a href='/' class='active'>User view</a><a href='/admin'>Admin view</a></nav>
    <div class='total-card'>
      <div><div class='label'>Total value</div><div class='big'>${total_value:,.2f}</div></div>
      <div><div class='label'>All-time gain</div><div class='big {gain_cls}'>${gain:+,.2f}</div></div>
    </div>
    <p class='note'>Test data only — no real money, no trading. Forecast is a learning model, not advice.</p>
    {cards or "<p>No holdings yet — add one below.</p>"}
    <section><h2>Add a holding</h2>
    <form method='post' action='/add'>
      <input name='ticker' placeholder='Ticker, e.g. AAPL' required>
      <input name='shares' type='number' step='any' placeholder='Shares' required>
      <input name='buy_price' type='number' step='any' placeholder='Price paid' required>
      <button>Add</button>
    </form></section>
    <section><h2>Look up one stock</h2>
    <form method='get' action='/lookup'>
      <input name='ticker' placeholder='Ticker, e.g. MSFT' required>
      <button>Look up</button>
    </form></section>
    <p style='margin-top:16px'><a href='/'>↻ Refresh prices</a></p>
    </div></body></html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    rows, tv, tc = portfolio_rows()
    return page(rows, tv, tc)

@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    if not admin_password():
        return HTMLResponse(login_page("No admin password is set on this computer yet. "
            "Set ADMIN_PASSWORD before starting the server, then refresh."))
    if not is_admin(request):
        return HTMLResponse(login_page())
    rows, tv, tc = portfolio_rows()
    return admin_page(rows, tv, tc)

@app.post("/admin/login")
def admin_login(password: str = Form(...)):
    pw = admin_password()
    if pw and password == pw:
        r = RedirectResponse("/admin", status_code=303)
        r.set_cookie("admin_auth", _auth_token(pw), httponly=True, samesite="lax")
        return r
    return HTMLResponse(login_page("Wrong password — try again."))

@app.get("/admin/logout")
def admin_logout():
    r = RedirectResponse("/", status_code=303)
    r.delete_cookie("admin_auth")
    return r

@app.post("/remove")
def remove(request: Request, ticker: str = Form(...)):
    if not is_admin(request):
        return RedirectResponse("/admin", status_code=303)
    p = tracker.load_portfolio(); p.pop(ticker.strip().upper(), None)
    tracker.save_portfolio(p)
    return RedirectResponse("/admin", status_code=303)

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
    return f"""<!doctype html><html><head><meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'><title>{t}</title>
    <style>{STYLE}</style></head><body><div class='wrap'>
    <header><h1>{t} — {name}</h1><p>Live price and 30-day trend forecast</p></header>
    <div class='total-card'><div><div class='label'>Live price</div>
    <div class='big'>${price:.2f}</div></div>
    <div><div class='label'>30-day forecast</div><div class='big'>${target:.2f}</div></div></div>
    <p>Range ${low:.2f} – ${high:.2f} · direction {direction}</p>
    <p class='note'>Learning model only — not financial advice.</p>
    <p><a href='/'>← Back to dashboard</a></p></div></body></html>"""
