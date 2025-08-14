import os
from dotenv import load_dotenv

import ccxt
import pandas as pd


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

binance = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret
})

ticker = binance.fetch_ticker('BTC/USDT')
print(f"Текущая цена BTC: {ticker['last']}")

# Получение книги ордеров (глубина рынка)
order_book = binance.fetch_order_book('BTC/USDT')
print(order_book)

# Получение исторических свечей (1-минутные)
ohlcv = binance.fetch_ohlcv('BTC/USDT', timeframe='1m', limit=10)
print(ohlcv)
