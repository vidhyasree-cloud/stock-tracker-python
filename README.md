# Stock Tracker — Python, step by step

Step 1: live prices + portfolio value + a simple trend forecast.
No API key. Data: Yahoo Finance chart API (public, free).
Forecast: average daily change over the last 30 days, projected 30 days
forward. A learning model only — NOT financial advice, NOT a trading signal.

## Run
```
pip install -r requirements.txt
python tracker.py
```
1 = add a holding (ticker, shares, buy price) — saved in `portfolio.json`
2 = show portfolio with live value + gain/loss + forecast
3 = look up one stock
4 = quit

## Next steps (later, one at a time)
Step 2: a real ML forecast (e.g. linear regression on closes, then compare it with this trend baseline)
Step 3: a web page for the tracker (FastAPI) instead of the terminal menu

## Step 3: web dashboard
```
uvicorn app:app --reload
```
Open http://127.0.0.1:8000 — total value, holdings, forecast, add-holding form, one-stock lookup.

## Admin password
User view (`/`) is open. Admin view (`/admin`) needs one password, set on
your own computer only — never in the code or on GitHub:
```powershell
$env:ADMIN_PASSWORD="your-password-here"
.\.venv\Scripts\uvicorn.exe app:app --reload
```
Then open /admin, type the password once, and it stays unlocked in that
browser until you tap "Log out of admin". If no password is set, /admin
tells you to set one first.
