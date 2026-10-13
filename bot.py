import os, time, requests, yfinance as yf, pandas as pd
from datetime import datetime
from flask import Flask
import threading
import pytz

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
CHAT_ID_FILE = "/tmp/chat_id.txt"

# S&P 500 top 100 most active to avoid 429 (full 500 triggers Yahoo block)
# We rotate through them
SP500_CORE = [
"AAPL","MSFT","NVDA","AMZN","META","GOOGL","BRK.B","LLY","AVGO","JPM",
"UNH","V","MA","HD","COST","PG","JNJ","ABBV","BAC","WMT",
"CRM","XOM","NFLX","KO","ORCL","MRK","CVX","ACN","AMD","LIN",
"PEP","TMO","CSCO","MCD","ABT","ADBE","WFC","QCOM","DHR","INTU",
"TXN","CAT","NOW","VZ","UNP","AMGN","IBM","GE","UBER","ISRG",
"SPG","GS","BLK","LOW","AMAT","BKNG","MS","EL","DE","AXP",
"SYK","TJX","GILD","ADI","ADP","MDLZ","LRCX","MMC","REGN","CB",
"CI","PLD","SCHW","CVS","ZTS","BDX","BSX","PGR","SO","NKE",
"DUK","EOG","SLB","COP","NEE","USB","ITW","HON","APD","SHW"
]

app = Flask(__name__)
@app.route('/')
def home(): return "v16 LIVE - Full Scanner Active"

def get_chat_id():
    global TELEGRAM_CHAT_ID
    if TELEGRAM_CHAT_ID: return TELEGRAM_CHAT_ID
    if os.path.exists(CHAT_ID_FILE):
        try:
            with open(CHAT_ID_FILE,'r') as f:
                cid = f.read().strip()
                if cid: return cid
        except: pass
    if not TELEGRAM_TOKEN: return None
    try:
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates", timeout=10).json()
        for update in r.get("result",[]):
            chat = update.get("message",{}).get("chat",{})
            cid = str(chat.get("id",""))
            if cid:
                with open(CHAT_ID_FILE,'w') as f: f.write(cid)
                print(f"Found Telegram chat: {cid} - SAVE THIS AS TELEGRAM_CHAT_ID ENV VAR!")
                return cid
    except Exception as e: print(f"get_chat error: {e}")
    return None

def send_telegram(msg):
    cid = get_chat_id()
    if not TELEGRAM_TOKEN or not cid:
        print(f"No Telegram setup: {msg[:80]}")
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                      json={"chat_id": cid, "text": msg, "parse_mode":"Markdown"}, timeout=10)
        print(f"SENT TELEGRAM to {cid}")
    except Exception as e: print(f"Telegram send error: {e}")

def is_market_open():
    et = pytz.timezone('US/Eastern')
    now = datetime.now(et)
    if now.weekday() >= 5: return False
    hm = now.hour*60 + now.minute
    return 570 <= hm <= 960 # 9:30 - 16:00

def check_breakout(ticker):
    try:
        # Anti-429: 1.2 sec delay per ticker
        time.sleep(1.2)
        df = yf.download(ticker, period="1mo", interval="1d", progress=False, auto_adjust=True)
        if len(df) < 22: return None
        # Flatten if multi-index
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        close = df['Close']
        vol = df['Volume']
        high_20 = close[-21:-1].max() # prev 20 days high
        avg_vol = vol[-21:-1].mean()
        
        last_close = float(close.iloc[-1])
        last_vol = float(vol.iloc[-1])
        
        if last_close > high_20 * 1.005 and last_vol > avg_vol * 1.3:
            return f"🚀 *{ticker}* BREAKOUT\nPrice: ${last_close:.2f} > 20D High ${high_20:.2f}\nVol: {last_vol/1e6:.1f}M vs Avg {avg_vol/1e6:.1f}M"
    except Exception as e:
        if "429" in str(e) or "Too Many" in str(e):
            print(f"429 hit on {ticker}, sleeping 60s")
            time.sleep(60)
        else:
            print(f"Error {ticker}: {e}")
    return None

def scanner_loop():
    print("=== BOT STARTED - v16 FULL SCANNER ===")
    send_telegram("✅ *Bot v16 Online!* Full S&P scanner active. Market hours 9:30-4 ET.")
    scan_count = 0
    while True:
        scan_count += 1
        now_et = datetime.now(pytz.timezone('US/Eastern')).strftime("%H:%M:%S")
        
        if not is_market_open():
            print(f"=== SCAN #{scan_count} at {now_et} - Market CLOSED (Weekend/After Hours) Heartbeat OK ===")
            time.sleep(300) # 5 min heartbeat when closed
            continue
        
        print(f"=== SCAN #{scan_count} at {now_et} - Market OPEN - Scanning ===")
        found = 0
        # Scan in batches of 10 to avoid 429
        for i in range(0, len(SP500_CORE), 10):
            batch = SP500_CORE[i:i+10]
            for ticker in batch:
                result = check_breakout(ticker)
                if result:
                    send_telegram(result)
                    found += 1
            if i+10 < len(SP500_CORE):
                print(f"Batch {i//10+1} done, sleeping 15s anti-429...")
                time.sleep(15)
        
        if found == 0:
            send_telegram(f"📊 Scan #{scan_count} {now_et} ET: No breakouts in top 100 S&P. Market open, watching.")
        
        print(f"Scan #{scan_count} finished, found {found}. Sleeping 10 min...")
        time.sleep(600) # 10 min between full scans

# Start scanner in background thread
threading.Thread(target=scanner_loop, daemon=True).start()

if __name__ == "__main__":
    print("🌿 v16 FINAL LIVE - Starting NOW...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
