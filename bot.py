import os
import time
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Tickers to scan - add yours
TICKERS = ["AAPL", "NVDA", "TSLA", "SPY", "QQQ", "MSFT", "AMD", "PLTR", "SOXL", "TQQQ"]

NY_TZ = pytz.timezone("America/New_York")

print("=== Green Bot v17 Clean - Starting ===")
print(f"Token set: {bool(TOKEN)}")
print(f"Chat ID set: {CHAT_ID if CHAT_ID else 'Not set yet - send /start to bot'}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"✅ Bot Connected!\n\nYour Chat ID is: {chat_id}\n\n"
        f"Go to Render -> Environment -> Add:\nTELEGRAM_CHAT_ID = {chat_id}\n\n"
        f"Then Save. You will get alerts automatically."
    )
    print(f"Found Telegram chat: {chat_id}")

async def scan_market():
    while True:
        now = datetime.now(NY_TZ)
        # Only scan during market hours 9:30 - 4pm ET, Mon-Fri
        if now.weekday() < 5 and 9 <= now.hour < 16:
            try:
                print(f"[{now.strftime('%H:%M:%S')}] Scanning {len(TICKERS)} tickers...")
                for ticker in TICKERS:
                    try:
                        data = yf.download(ticker, period="2d", interval="15m", progress=False)
                        if data.empty or len(data) < 20:
                            continue
                        # Simple breakout example: price above previous day high + volume
                        last_close = float(data['Close'].iloc[-1])
                        prev_high = float(data['High'].iloc[-21:-1].max()) if len(data) > 21 else float(data['High'].max())
                        
                        if last_close > prev_high * 1.01: # 1% breakout
                            msg = f"🚀 BREAKOUT: {ticker} @ ${last_close:.2f}\nAbove prev high ${prev_high:.2f}"
                            print(msg)
                            # Send if CHAT_ID is set
                            if CHAT_ID:
                                try:
                                    app = ApplicationBuilder().token(TOKEN).build()
                                    await app.bot.send_message(chat_id=int(CHAT_ID), text=msg)
                                except Exception as e:
                                    print(f"Send error: {e}")
                    except Exception as e:
                        print(f"{ticker} error: {e}")
                        continue
            except Exception as e:
                print(f"Scan loop error: {e}")
        
        await asyncio.sleep(60) # scan every 60 sec

async def main():
    # Build Telegram app
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot v17 Online! Listening for /start...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Start scanning loop
    await scan_market()

if __name__ == "__main__":
    asyncio.run(main())
