from dotenv import load_dotenv
import ccxt
import os
import pandas as pd
import datetime
import time

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,  # helps prevent rate-limit issues
})

symbol = 'BTC/USDT'
timeframe = '1m'

start_time = int(datetime.datetime(2024, 1, 1, 0, 0).timestamp() * 1000)
end_time = int(datetime.datetime(2025, 6, 1, 0, 0).timestamp() * 1000)

all_ohlcv = []
since = start_time

while since < end_time:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
    if not ohlcv:
        break
    all_ohlcv.extend(ohlcv)
    since = ohlcv[-1][0] + 1  # move to next timestamp
    time.sleep(exchange.rateLimit / 1000)  # respect rate limit

# Create DataFrame
df = pd.DataFrame(all_ohlcv, columns=[
    'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume'
])

# Convert timestamp and types
#df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
    df[col] = df[col].astype(float)

print(df.head(), df.tail())

df.to_csv('backtest_data_btc_usdt_1m.csv', index=False)
