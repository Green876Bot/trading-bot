import os, threading, time
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

TOKEN = os.getenv("TELEGRAM_TOKEN","").strip()
print(f"=== Green Bot v18 FINAL - Token OK: {bool(TOKEN)} ===")

# Flask to keep Render Web Service alive
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Bot is Live! Send /start to @Green876Bot"

# Telegram handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    print(f"!!! GOT /start from {cid} !!!")
    await update.message.reply_text(
        f"✅ BOT IS LIVE!\n\nYour Chat ID is: {cid}\n\nNow go to Render -> Environment -> Add:\nTELEGRAM_CHAT_ID = {cid}\n\nYou will get alerts!"
    )

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

async def run_telegram():
    print("Telegram polling started - Send /start now!")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

def start_threads():
    # Start Flask in background thread
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    # Run Telegram polling (main)
    asyncio.run(run_telegram())

if __name__ == "__main__":
    start_threads()
