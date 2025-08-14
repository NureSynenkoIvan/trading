import ccxt
import numpy as np
import talib
import requests
import time

from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

binance = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'options': {'defaultType': 'future'}
})

def log_info(text):
    print(text)

def get_top_coins():
    futures_pairs = [s for s in binance.load_markets() if '/USDT' in s]
    top_coins = []
    
    for symbol in futures_pairs:
        try:
            log_info("Analyzing symbol:" + symbol)
            ticker = binance.fetch_ticker(symbol)
            ohlcv = binance.fetch_ohlcv(symbol, timeframe='5m', limit=12)
            closes = np.array([c[4] for c in ohlcv])
            volume = ticker['quoteVolume']
            volatility = (max(closes) - min(closes)) / min(closes) * 100

            if volume > 50000000 and volatility > 1.5:
                top_coins.append((symbol, volatility, volume))
        except:
            continue

    top_coins.sort(key=lambda x: x[1], reverse=True)
    return top_coins[:5]

def check_entry(symbol):
    ohlcv = binance.fetch_ohlcv(symbol, timeframe='5m', limit=50)
    closes = np.array([c[4] for c in ohlcv])
    ema7 = talib.EMA(closes, timeperiod=9)
    ema25 = talib.EMA(closes, timeperiod=21)
    rsi = talib.RSI(closes, timeperiod=14)

    if ema7[-1] > ema25[-1] and 30 < rsi[-1] < 60:
        return "BUY"
    elif ema7[-1] < ema25[-1] and 40 < rsi[-1] < 70:
        return "SELL"
    return None

def manage_trade(symbol, side, entry_price):
    sl = entry_price * 0.985  # SL -1.5%
    tp1 = entry_price * 1.01  # TP1 +1%
    tp2 = entry_price * 1.02  # TP2 +2%

    # Устанавливаем TP1 (фиксируем 30%)
    binance.create_limit_order(symbol, side, 0.3, tp1)
    log_info(f"🔵 TP1 установлен на {tp1}")

    # Устанавливаем TP2 (фиксируем 50%)
    binance.create_limit_order(symbol, side, 0.5, tp2)
    log_info(f"🔵 TP2 установлен на {tp2}")

    # Trailing Stop на оставшиеся 20%
    trailing_stop = entry_price * 1.015
    binance.create_order(symbol, 'trailingStopMarket', side, 0.2, trailing_stop)
    log_info(f"🔵 Trailing Stop установлен на {trailing_stop}")

while True:
    top_coins = get_top_coins()
    log_info(f"🔥 ТОП монеты: {[coin[0] for coin in top_coins]}")

    """
    for coin in top_coins:
        entry_signal = check_entry(coin[0])
        if entry_signal:
            log_info(f"📈 Сигнал {entry_signal} для {coin[0]}")
            entry_price = binance.fetch_ticker(coin[0])['last']
            manage_trade(coin[0], entry_signal.lower(), entry_price)"""

