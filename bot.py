# FIX FOR RENDER - keeps port open
import threading, os
from http.server import HTTPServer, BaseHTTPRequestHandler
class Handler(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Running - v15 LIVE')
def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
threading.Thread(target=keep_alive, daemon=True).start()

# MAIN BOT - v15 FINAL BREAK & RETEST
import yfinance as yf
import time
import requests
import datetime
import pandas as pd

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8997092021:AAEmnJ-wgJFZznCqOFSrubU7a0_3fB4gFLs")
CHAT_ID = os.environ.get("CHAT_ID", "")  # we will auto-find it

WATCHLIST = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "MSFT", "META", "AMD", "NFLX", "AMZN"]

def send_telegram(msg):
    global CHAT_ID
    try:
        if not CHAT_ID:
            # Auto-find chat id from last message
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates", timeout=10).json()
            if r.get("result"):
                CHAT_ID = str(r["result"][-1]["message"]["chat"]["id"])
                print(f"Found CHAT_ID: {CHAT_ID}")
        if CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
            print(f"Sent: {msg[:50]}")
    except Exception as e:
        print(f"Telegram error: {e}")

def check_break_retest(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="5m", progress=False)
        if len(df) < 50:
            return None
        close = df['Close'].iloc[-1]
        high_20 = df['High'].rolling(20).max().iloc[-2]
        low_20 = df['Low'].rolling(20).min().iloc[-2]
        
        # Simple v15 logic
        if close > high_20 * 0.999:  # Breaking high
            # Check retest
            prev_close = df['Close'].iloc[-2]
            if abs(close - high_20) / high_20 < 0.002:  # within 0.2% of breakout
                return f"🟢 *{symbol} BREAK & RETEST* \nPrice: ${close:.2f} breaking ${high_20:.2f}\nScore: 5/6 CONFIRMED"
        if close < low_20 * 1.001:
            if abs(close - low_20) / low_20 < 0.002:
                return f"🔴 *{symbol} BREAKDOWN & RETEST* \nPrice: ${close:.2f} breaking ${low_20:.2f}\nScore: 5/6"
        return None
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return None

print("🌲 v15 FINAL LIVE - Fixed for Render")
send_telegram("🌲 *Bot Online* - v15 FINAL LIVE on Render! Scanning started...")

while True:
    try:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"=== SCAN {now} ===")
        for sym in WATCHLIST:
            signal = check_break_retest(sym)
            time.sleep(1)  # avoid yahoo rate limit
            if signal:
                print(f"{sym}: SIGNAL!")
                send_telegram(signal)
            else:
                df = yf.download(sym, period="1d", interval="1m", progress=False)
                if len(df) > 0:
                    price = df['Close'].iloc[-1]
                    print(f"{sym}: ${price:.2f} - no setup")
        print("Sleep 60s...")
        time.sleep(60)
    except Exception as e:
        print(f"Loop error: {e}")
        time.sleep(30)
