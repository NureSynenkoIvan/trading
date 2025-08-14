import ccxt
import numpy as np
import talib
import time
from dotenv import load_dotenv
import os
import time
import logging

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

binance = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'options': {'defaultType': 'spot'}
})


logging.basicConfig(filename="trading_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")


def listening_mode(stop_loss_percent, take_profit_percent, symbols):
    while (True):
        for sym in symbols:
            ohlcv = binance.fetch_ohlcv(sym, timeframe='1s', limit=25)

            closes = np.array([candle[4] for candle in ohlcv])

            ema7 = talib.EMA(closes, timeperiod=7)
            ema25 = talib.EMA(closes, timeperiod=25)

            rsi_ohlcv = binance.fetch_ohlcv(sym, timeframe='1m', limit=20)
            rsi_closes = np.array([candle[4] for candle in rsi_ohlcv])
            rsi = talib.RSI(rsi_closes, timeperiod=14)

            if ema7[-1] > ema25[-1] and rsi[-1] < 40:
                print(f"Сигнал на ЛОНГ! Символ: {sym}")
                entry_price = (binance.fetch_ticker(sym))['last']
                stop_loss = entry_price * (1 - (stop_loss_percent / 100))
                take_profit = entry_price * (1 + (take_profit_percent / 100))
                print(f"Цена входа: {closes[-1]}")
                print(f"Стоп-лосс: {stop_loss}")
                print(f"Тейк-профит: {take_profit}")
                logging.info(f"Entering the position symbol: {sym}, price = {closes[-1]}, stop_loss = {stop_loss}, take_profit = {take_profit} rsi = {rsi[-1]}")
                trading_mode(stop_loss=stop_loss, take_profit=take_profit, symbol=sym)
                break
            elif ema7[-1] < ema25[-1] and rsi[-1] > 65:
                print("Сигнал на ШОРТ!")
            else:
                print("Без когерентного сигнала, символ: " + sym +" " + "ema7: " + str(ema7[-1]) +", ema25: " + str(ema25[-1]) + ", rsi: "+ str(rsi[-1]))
        time.sleep(1)
        

def trading_mode(stop_loss, take_profit, symbol):
    global exits_stop_loss
    global exits_take_profit
    while (True):
        tick = binance.fetch_ticker(symbol)
        price = tick['last']
        if (price >= take_profit):
            exits_take_profit += 1
            print("Успешный выход по тейк-профиту!")
            logging.info(f"Exit on take_profit, symbol: {symbol}, price: {price}")
            logging.info(f"Exits on stop_loss: {exits_stop_loss}, exits on take_profit: {exits_take_profit}")
            return
        elif(price <= stop_loss):
            exits_stop_loss += 1
            print("Успешный выход по стоп-лоссу!")
            logging.info(f"Exit on stop_loss, symbol: {symbol}, price: {price}")
            logging.info(f"Exits on stop_loss: {exits_stop_loss}, exits on take_profit: {exits_take_profit}")
            return
        else:
            print(f"Waiting, current price: {price}")
        time.sleep(1)





slp = 0.2
tpp = 0.4

symbols = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'BNB/USDT']



exits_stop_loss = 0
exits_take_profit = 0

listening_mode(stop_loss_percent=slp, take_profit_percent=tpp, symbols=symbols)


