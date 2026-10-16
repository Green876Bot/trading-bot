import os, time, threading, requests
from flask import Flask
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN","").strip()
print(f"=== Green Bot v19 - FIXED FOR PYTHON 3.14 ===")
print(f"Token OK: {bool(TOKEN)}")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live! Go to Telegram @Green876Bot and send /start"

def telegram_polling():
    print("Starting Telegram polling with requests...")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            r = requests.get(url, params={"offset": offset, "timeout": 30}, timeout=35)
            data = r.json()
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    chat_id = msg.get("chat", {}).get("id")
                    print(f"Got message: {text} from {chat_id}")
                    if text == "/start" and chat_id:
                        # Reply
                        send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                        reply = f"✅ BOT IS LIVE!\n\nYour Chat ID is: {chat_id}\n\nGo to Render -> Environment -> Add:\nTELEGRAM_CHAT_ID = {chat_id}"
                        requests.post(send_url, json={"chat_id": chat_id, "text": reply})
                        print(f"Replied to {chat_id}")
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
        time.sleep(2)

def heartbeat():
    count = 0
    while True:
        count += 1
        print(f"=== SCAN #{count} at {datetime.now().strftime('%H:%M:%S')} - Bot alive - Send /start to test ===")
        time.sleep(60)

if __name__ == "__main__":
    # Start polling in background
    threading.Thread(target=telegram_polling, daemon=True).start()
    threading.Thread(target=heartbeat, daemon=True).start()
    # Start Flask
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)
