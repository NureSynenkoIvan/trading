import ccxt
import numpy as np
import talib
import time
from dotenv import load_dotenv
import os
import time
import logging

import pandas as pd


def perform_strategy(fetch_data_strategy, process_data_strategy, trade_strategy):
    data = fetch_data(fetch_data_strategy)
    sygnals = process_data(strategy=process_data_strategy, data=data)
    trade_strategy(sygnals, data)

def fetch_data(strategy):
    return strategy()

def process_data(strategy, data):
    strategy(data)



def binance_fetch_strategy():
    ohlcv = binance.fetch_ohlcv("BTC/USDT", timeframe='1m', limit=25)
    closes = np.array([candle[4] for candle in ohlcv])
    return closes

def grok_process_data_strategy(data):
    pass


def old_process_data_strategy(data):
    if len(data) < 25:
        return ""

    ema7 = talib.EMA(data, timeperiod=7)
    ema25 = talib.EMA(data, timeperiod=25)
    rsi = talib.RSI(data, timeperiod=14)
    
    sygnal = ""

    if ema7[-1] > ema25[-1] and rsi[-1] < 40:
        sygnal = "LONG"
        print("LONG sygnal caught")
    elif ema7[-1] < ema25[-1] and rsi[-1] > 70:
        sygnal = "SHORT"
        print("SHORT sygnal caught")
    else:
        print("no sygnal caught")

    return sygnal

def old_trade_strategy(sygnal, data):
    if (sygnal == "LONG"):
        symbol = "BTC/USDT"
        stop_loss_percent = 1
        take_profit_percent = 2

        entry_price = (binance.fetch_ticker(symbol))['last']
        stop_loss = entry_price * (1 - (stop_loss_percent / 100))
        take_profit = entry_price * (1 + (take_profit_percent / 100))

        rsi = talib.RSI(data, timeperiod=14)

        print(f"Цена входа: {data[-1]}")
        print(f"Стоп-лосс: {stop_loss}")
        print(f"Тейк-профит: {take_profit}")


        logging.info(f"Entering the position symbol: {symbol}, price = {data[-1]}, stop_loss = {stop_loss}, take_profit = {take_profit} rsi = {rsi[-1]}")

    
        while (True):
            tick = binance.fetch_ticker("BTC/USDT")
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
    else:
        return


def read_historical_data_file(file_path):
    column_names = [
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ]
    df = pd.read_csv(file_path, header=None, names=column_names)

    df['open_time'] = df['open_time'] // 1000
    df['close_time'] = df['close_time'] // 1000

    ohlcv_df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']].copy()
    ohlcv_df['open_time'] = pd.to_datetime(ohlcv_df['open_time'], unit='ms')
    ohlcv_df.sort_values('open_time', inplace=True)
    ohlcv_df.reset_index(drop=True, inplace=True)
    
    print(ohlcv_df.head())

    return ohlcv_df

def backtest_fetch_strategy(ohlcv_dataframe, iterator_position, window=30):
    if iterator_position < window:
        return None
    closes = ohlcv_dataframe['close'].iloc[iterator_position - window:iterator_position].to_numpy(dtype=np.float64)
    
    if np.isnan(closes).any():
        print("Предупреждение: в данных есть NaN значения")
        closes = np.nan_to_num(closes, nan=np.nanmean(closes))
    if len(closes) < window:
        print(f"Предупреждение: недостаточно данных. Требуется {window}, получено {len(closes)}")
    return closes
    
def backtest_old_enter_trade_strategy(sygnal, data):
    pass

def backtest_old_execute_trade_strategy(data):
    pass

def backtest_mock_enter_trade_strategy(sygnal, data):
    if sygnal == "LONG":
        logging.info("LONG")
    elif sygnal == "SHORT":
        logging.info("SHORT")
    return False



def grind_strategy_performance(fetch_data_strategy, process_data_strategy, trade_strategy, seconds):
    while(True):
        try: 
            perform_strategy(fetch_data_strategy, process_data_strategy, trade_strategy)
        except Exception:
            time.sleep(1)
            perform_strategy(fetch_data_strategy, process_data_strategy, trade_strategy)
        finally:
            time.sleep(seconds)


def backtest_strategy_performance(backtest_data_source, backtest_fetch_data_strategy, process_data_strategy, backtest_trade_strategy):
    
    ohlcv_df = read_historical_data_file(backtest_data_source)

    #Starting in normal mode
    in_trading_mode = False

    #25 is chosen because we use 30 rows info at most
    for i in range(30, len(ohlcv_df)):
        if (not in_trading_mode):
            data = backtest_fetch_data_strategy(ohlcv_df, i)
            sygnals = process_data(process_data_strategy, data)
            in_trading_mode = backtest_mock_enter_trade_strategy(sygnals, data)
        else:
            data = backtest_fetch_data_strategy(ohlcv_df, i)
        



# ====================== PROGRAM EXECUTION ======================


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


#grind_strategy_performance(binance_fetch_strategy, old_process_data_strategy, old_trade_strategy, 60)



folder_path = "C:\\Users\\User\\Documents\\python-projects\\trading\\v4\\backtest_data"

for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        logging.info(filename)
        file_path = os.path.join(folder_path, filename)
        backtest_strategy_performance(file_path, backtest_fetch_strategy, old_process_data_strategy, "")
        