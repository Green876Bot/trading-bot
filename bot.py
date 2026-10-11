import threading, os
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Running - v15 LIVE - Fixed!')
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

import time, requests, datetime
print("🌲 v15 FINAL LIVE - Starting NOW...", flush=True)

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_FILE = "/tmp/chat_id.txt"

def get_chat():
    if os.path.exists(CHAT_FILE):
        return open(CHAT_FILE).read().strip()
    return ""

def save_chat(cid):
    open(CHAT_FILE, 'w').write(str(cid))

def send_tele(msg):
    try:
        cid = get_chat()
        if not cid and TOKEN:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", timeout=15).json()
            if r.get("result"):
                for u in reversed(r["result"]):
                    if "message" in u:
                        cid = str(u["message"]["chat"]["id"])
                        save_chat(cid)
                        break
        if cid and TOKEN:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": cid, "text": msg}, timeout=10)
            print(f"SENT TELEGRAM to {cid}", flush=True)
    except Exception as e:
        print(f"Tele error: {e}", flush=True)

time.sleep(2)
print("=== BOT STARTED ===", flush=True)
send_tele("Bot Online! I can see logs now. Market closed today.")

c = 0
while True:
    try:
        c += 1
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"=== SCAN #{c} at {now} - Heartbeat OK - Weekend, no stocks today ===", flush=True)
        time.sleep(60)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(10)
