import yfinance as yf, pandas as pd, requests, numpy as np
from scipy.signal import argrelextrema
import time, os
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8997092021:AAEmnJ-wgJFZznCqOFSrubU7a0_3fB4gFLs")
TELEGRAM_CHAT_ID = "8852039470"
TICKERS = ["SPY","QQQ","AMD","TSLA","META","NVDA","BE","MU","AAPL","MSFT","PLTR","SPCX","CRWV","QCOM","CRCL","MSTR","COIN","LYFT","UBER","ARM","HOOD"]
break_levels = {}

def send_telegram(msg):
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id":TELEGRAM_CHAT_ID,"text":msg}, timeout=10)
    except: pass
    print(msg)

def analyze_ticker(ticker):
    try:
        df=yf.download(ticker,period="10d",interval="15m",progress=False,auto_adjust=True)
        if len(df)<100: return None
        df.columns=df.columns.get_level_values(0) if isinstance(df.columns,pd.MultiIndex) else df.columns
        price=df['Close'].iloc[-1]
        highs=df['High'].tail(150); lows=df['Low'].tail(150)
        high_idx=argrelextrema(highs.values,np.greater,order=5)[0]
        low_idx=argrelextrema(lows.values,np.less,order=5)[0]
        if len(high_idx)<2 or len(low_idx)<2: return None
        sh1=highs.iloc[high_idx[-1]]; sh2=highs.iloc[high_idx[-2]]
        sl1=lows.iloc[low_idx[-1]]; sl2=lows.iloc[low_idx[-2]]
        is_break=False; is_retest=False; is_failed_retest=False
        break_level=None; direction=None; trade_type=None
        if df['Close'].tail(20).max() > sh2 and price > sh2*0.997:
            if ticker not in break_levels or break_levels[ticker]['level']!= sh2:
                break_levels[ticker] = {'level': sh2, 'dir': 'BULL', 'time': datetime.now(), 'tested': False}
                is_break = True; break_level = sh2; direction = "BULL"
        if df['Close'].tail(20).min() < sl2 and price < sl2*1.003:
            if ticker not in break_levels or break_levels[ticker]['level']!= sl2:
                break_levels[ticker] = {'level': sl2, 'dir': 'BEAR', 'time': datetime.now(), 'tested': False}
                is_break = True; break_level = sl2; direction = "BEAR"
        if ticker in break_levels:
            stored = break_levels[ticker]; lvl = stored['level']
            if stored['dir'] == 'BULL':
                if abs(price - lvl)/lvl < 0.0035 and price >= lvl:
                    last3 = df['Low'].tail(3)
                    if (last3 >= lvl*0.998).all() or (last3 >= lvl*0.995).sum() >=2:
                        is_retest = True; is_break = True; break_level = lvl; direction = "BULL"; trade_type = "CALLS"; stored['tested'] = True
                if price < lvl*0.998 and not stored.get('tested', False):
                    if df['High'].tail(10).max() > lvl:
                        is_failed_retest = True; break_level = lvl; direction = "BULL_FAILED"; trade_type = "PUTS"; is_break = True
            if stored['dir'] == 'BEAR':
                if abs(price - lvl)/lvl < 0.0035 and price <= lvl:
                    last3 = df['High'].tail(3)
                    if (last3 <= lvl*1.002).all():
                        is_retest = True; break_level = lvl; direction = "BEAR"; trade_type = "PUTS"; stored['tested'] = True
                if price > lvl*1.002 and not stored.get('tested', False):
                    if df['Low'].tail(10).min() < lvl:
                        is_failed_retest = True; break_level = lvl; direction = "BEAR_FAILED"; trade_type = "CALLS"; is_break = True
        swing_low = sl1; swing_high = sh1
        if break_level:
            if direction in ["BULL", "BULL_FAILED"]: swing_high = max(sh1, break_level)
            else: swing_low = min(sl1, break_level)
        if swing_high <= swing_low: return None
        diff = swing_high - swing_low
        fib_618 = swing_high - diff*0.618; fib_786 = swing_high - diff*0.786
        at_golden = (fib_786 <= price <= fib_618)
        at_fvg=False
        for i in range(len(df)-10,len(df)-1):
            if df['Low'].iloc[i] > df['High'].iloc[i-2] and df['High'].iloc[i-2] <= price <= df['Low'].iloc[i]:
                at_fvg=True; break
        at_ob=False
        for j in range(len(df)-30,len(df)-3):
            if df['Low'].iloc[j] <= price <= df['High'].iloc[j]:
                at_ob=True; break
        close=df['Close']; delta=close.diff()
        gain=delta.where(delta>0,0).ewm(alpha=1/14).mean()
        loss=-delta.where(delta<0,0).ewm(alpha=1/14).mean()
        rsi=100-(100/(1+gain/loss)); rsi_now=rsi.iloc[-1]
        ema9=close.ewm(span=9).mean().iloc[-1]; ema21=close.ewm(span=21).mean().iloc[-1]
        score = (2 if is_retest else 0) + (2 if is_failed_retest else 0) + (1 if is_break else 0) + (1 if at_golden else 0) + (1 if at_ob or at_fvg else 0) + (1 if ema9>ema21 else 0)
        return {'ticker':ticker,'price':price,'rsi':rsi_now,'score':score,'swing_low':swing_low,'swing_high':swing_high,'fib_618':fib_618,'at_golden':at_golden,'is_break':is_break,'is_retest':is_retest,'is_failed_retest':is_failed_retest,'break_level':break_level,'direction':direction,'trade_type':trade_type,'at_ob':at_ob,'at_fvg':at_fvg}
    except: return None

def scan_all():
    print(f"\n=== SCAN {datetime.now().strftime('%H:%M:%S')} ===")
    for ticker in TICKERS:
        sig=analyze_ticker(ticker)
        if not sig: continue
        status = "🔥 RETEST" if sig['is_retest'] else ("💀 FAILED" if sig['is_failed_retest'] else ("💥 BREAK" if sig['is_break'] else ""))
        print(f"{sig['ticker']}: ${sig['price']:.2f} {sig['score']}/6 {status}")
        if sig['is_retest'] and sig['score']>=4:
            msg=f"💎💎💎 BREAK & RETEST {sig['trade_type']} {sig['ticker']} ${sig['price']:.2f}\nBroke ${sig['break_level']:.2f} Retest holding\nTarget $1000 Lock $300"
            send_telegram(msg)
        elif sig['is_failed_retest'] and sig['score']>=4:
            msg=f"💀💀💀 FAILED BREAK {sig['trade_type']} {sig['ticker']} ${sig['price']:.2f}\nFailed ${sig['break_level']:.2f} Trap! {sig['trade_type']} now"
            send_telegram(msg)
        elif sig['is_break'] and not sig['is_retest']:
            msg=f"💥 BREAK {sig['ticker']} ${sig['price']:.2f} {sig['direction']} ${sig['break_level']:.2f}\nWatching retest"
            send_telegram(msg)

send_telegram(f"🌲 v15 FINAL LIVE - BREAK+RETEST + FAILED + $1000\n{', '.join(TICKERS)}")
while True:
    try: scan_all()
    except Exception as e: print(e)
    time.sleep(120)
