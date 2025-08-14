import ccxt
import numpy as np
import talib
import time
from dotenv import load_dotenv
import os
import time
import logging
import pandas as pd


class TradeStrategy:
    def __init__(self):
        pass
    
    def process_data(data):
        sygnal = None
        return sygnal

    def enter_trading_mode(self, sygnal, data):
        pass

    def execute_training_mode(self):
        pass 
    
class OldStrategy(TradeStrategy):
    def __init__(self, binance=None):
        self.binance = binance
        self.stop_loss_percent = 1
        self.take_profit_percent = 2
        self.symbol = "BTC/USDT"
        self.exits_stop_loss = 0
        self.exits_take_profit = 0

        logging.basicConfig(filename="v5\\trading_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")


    def process_data(self, data):           
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

    def enter_trading_mode(self, sygnal, data):
        if (sygnal == "LONG"):
            entry_price = data[-1]
            self.stop_loss = entry_price * (1 - (self.stop_loss_percent / 100))
            self.take_profit = entry_price * (1 + (self.take_profit_percent / 100))

            rsi = talib.RSI(data, timeperiod=14)

            print(f"Цена входа: {data[-1]}")
            print(f"Стоп-лосс: {self.stop_loss}")
            print(f"Тейк-профит: {self.take_profit}")


            logging.info(f"Entering the position symbol: {self.symbol}, price = {data[-1]}, stop_loss = {self.stop_loss}, take_profit = {self.take_profit} rsi = {rsi[-1]}")
            in_trading_mode = True      
        else:
            in_trading_mode = False
        return in_trading_mode

    def execute_trading_mode(self, data):
        in_trading_mode = True

        price = data[-1]
        if (price >= self.take_profit):
            self.exits_take_profit += 1
            print("Успешный выход по тейк-профиту!")
            logging.info(f"Exit on take_profit, symbol: {self.symbol}, price: {price}")
            logging.info(f"Exits on stop_loss: {self.exits_stop_loss}, exits on take_profit: {self.exits_take_profit}")
            in_trading_mode = False
        elif(price <= self.stop_loss):
            self.exits_stop_loss += 1
            print("Успешный выход по стоп-лоссу!")
            logging.info(f"Exit on stop_loss, symbol: {self.symbol}, price: {price}")
            logging.info(f"Exits on stop_loss: {self.exits_stop_loss}, exits on take_profit: {self.exits_take_profit}")
            in_trading_mode = False
        else:
            print(f"Waiting, current price: {price}")
        return in_trading_mode 




class FetchStrategy:
    def __init__(self):
        pass
    
    def fetch_data(self):
        pass

    def fetch_data_backtest(self):
        pass

    def start_backtest(self, backtest_data_file_path):
        pass


class BinanceFetchStrategy(FetchStrategy):
    def __init__(self, backtest_data_file_path=None):
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        self.binance = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'spot'}
        })
        self.backtest_data_file_path = backtest_data_file_path

        self.ohlcv_df = None
        self.current_index = 30

    def fetch_data(self):
        ohlcv = self.binance.fetch_ohlcv("BTC/USDT", timeframe='1m', limit=25)
        closes = np.array([candle[4] for candle in ohlcv])
        return closes
    
    def fetch_data_backtest(self):
        if self.ohlcv_df is None:
           self.ohlcv_df = self.read_historical_data_file(self.backtest_data_file_path) 
        if self.current_index < len(self.ohlcv_df):
            data_slice = self.ohlcv_df.iloc[self.current_index - 25:self.current_index]
            self.current_index += 1
            return data_slice['close'].to_numpy(dtype=np.float64)
            
        else:
            raise StopIteration("No more backtest data available.")
        
    def start_backtest(self, backtest_data_file_path):
        self.backtest_data_file_path = backtest_data_file_path
        self.ohlcv_df = self.read_historical_data_file(backtest_data_file_path)
        self.current_index = 30

    def read_historical_data_file(self, file_path):
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







class StrategyExecutor:
    def __init__(self, fetching_strategy, trading_strategy):
        self.fetching_strategy = fetching_strategy
        self.trading_strategy = trading_strategy

    def execute(self, timing):
        #Starting not in position
        in_trading_mode = False

        while(True):
            try: 
                if (not in_trading_mode):
                    data = self.fetching_strategy.fetch_data()
                    sygnals = self.trading_strategy.process_data(data)
                    in_trading_mode = self.trading_strategy.enter_trading_mode(sygnals, data)
                else:
                    data = self.fetching_strategy.fetch_data()
                    in_trading_mode = self.trading_strategy.execute_trading_mode(data)
            except Exception:
                time.sleep(1)
                continue
            time.sleep(timing)
    
    def execute_backtest(self, backtest_file_path):
        self.fetching_strategy.start_backtest(backtest_file_path)
        try:
            in_trading_mode = False
            while True:
                if not in_trading_mode:
                    data = self.fetching_strategy.fetch_data_backtest()
                    sygnals = self.trading_strategy.process_data(data)
                    in_trading_mode = self.trading_strategy.enter_trading_mode(sygnals, data)
                else:
                    data = self.fetching_strategy.fetch_data_backtest()
                    in_trading_mode = self.trading_strategy.execute_trading_mode(data)
        except StopIteration:
            print("Backtest finished.")



def main():
    folder_path = "C:\\Users\\User\\Documents\\python-projects\\trading\\v5\\backtest_data_new"
    
    backtest_files = [
        os.path.join(folder_path, filename)
        for filename in os.listdir(folder_path)
        if filename.endswith(".csv")
    ]

    fetching_strategy = BinanceFetchStrategy()
    trading_strategy = OldStrategy()
    trading_strategy.binance = fetching_strategy.binance
    executor = StrategyExecutor(fetching_strategy, trading_strategy)

    for path in backtest_files:
        print(f"Running backtest for {path}")
        executor.execute_backtest(path)

if __name__ == "__main__":
    main()