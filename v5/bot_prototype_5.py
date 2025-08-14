import ccxt
import numpy as np
import talib
import time
from dotenv import load_dotenv
import os
import time
import logging
import pandas as pd

def purchase(amount_of_original_money, price):
    return amount_of_original_money / price

def sell (tokens_to_sell, price):
    return tokens_to_sell * price

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

    

class BacktestInfo:
    def __init__(self, starting_money=1000, exchange_commission=0):
        self.exits_stop_loss = 0
        self.exits_take_profit = 0
        self.starting_money = starting_money
        self.current_money=starting_money
        self.target_tokens = 0
        self.exchange_commission=exchange_commission
    
    def on_take_profit(self):
        self.exits_take_profit+=1
    
    def on_stop_loss(self):
        self.exits_stop_loss+=1

    def on_buy(self, amount_to_spend, price) : 
        self.current_money -= amount_to_spend
        number_of_target_tokens = purchase(amount_to_spend - self.exchange_commission, price)
        self.target_tokens += number_of_target_tokens
    
    def on_sell(self, amount_to_sell, price):
        self.target_tokens -= amount_to_sell
        self.current_money += sell(amount_to_sell - self.exchange_commission, price=price)

    def calculate_profitability(self):
        percents_from_original = self.current_money / (self.starting_money / 100)
        return percents_from_original - 100



class OldStrategy(TradeStrategy):
    def __init__(self, binance=None, stop_loss_percent=1, take_profit_percent=2):
        self.binance = binance
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.symbol = "BTC/USDT"
        self.backtest_info = BacktestInfo()

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


            self.backtest_info.on_buy(self.backtest_info.current_money, data[-1])
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
            self.backtest_info.on_take_profit()
            self.backtest_info.on_sell(self.backtest_info.current_money, price=price)
            print("Успешный выход по тейк-профиту!")
            logging.info(f"Exit on take_profit, symbol: {self.symbol}, price: {price}")
            logging.info(f"Exits on stop_loss: {self.backtest_info.exits_stop_loss}, exits on take_profit: {self.backtest_info.exits_take_profit}")
            in_trading_mode = False
        elif(price <= self.stop_loss):
            self.backtest_info.on_stop_loss()
            self.backtest_info.on_sell(self.backtest_info.target_tokens, price)
            print("Успешный выход по стоп-лоссу!")
            logging.info(f"Exit on stop_loss, symbol: {self.symbol}, price: {price}")
            logging.info(f"Exits on stop_loss: {self.backtest_info.exits_stop_loss}, exits on take_profit: {self.backtest_info.exits_take_profit}")
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
            return data_slice['Close'].to_numpy(dtype=np.float64)
            
        else:
            raise StopIteration("No more backtest data available.")
        
    def start_backtest(self, backtest_data_file_path):
        self.backtest_data_file_path = backtest_data_file_path
        self.ohlcv_df = self.read_historical_data_file(backtest_data_file_path)
        self.current_index = 30

    def read_historical_data_file(self, file_path):
        column_names = [
            'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume'
        ]
        df = pd.read_csv(file_path, header=None, names=column_names)

        ohlcv_df = df[['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()
        #ohlcv_df['Open Time'] = pd.to_datetime(ohlcv_df['Open Time'], unit='ms')
        #ohlcv_df.sort_values('Open Time', inplace=True)
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
    
    def execute_backtest(self, backtest_file_path, money=1000):
        self.fetching_strategy.start_backtest(backtest_file_path)
        self.trading_strategy.starting_money=1000
        self.trading_strategy.current_money=1000
        try:
            in_trading_mode = False
            data = []
            while True:
                if not in_trading_mode:
                    data = self.fetching_strategy.fetch_data_backtest()
                    sygnals = self.trading_strategy.process_data(data)
                    in_trading_mode = self.trading_strategy.enter_trading_mode(sygnals, data)
                else:
                    data = self.fetching_strategy.fetch_data_backtest()
                    in_trading_mode = self.trading_strategy.execute_trading_mode(data)
        except StopIteration:
            logging.info("Backtest finished.")
            if (self.trading_strategy.backtest_info.target_tokens > 0):
                self.trading_strategy.backtest_info.on_sell(self.trading_strategy.backtest_info.target_tokens, data[-1])
            logging.info(f"Starting money: {self.trading_strategy.backtest_info.starting_money}")
            logging.info(f"Current_money: {self.trading_strategy.backtest_info.current_money}")
            logging.info(f"Profitability: {self.trading_strategy.backtest_info.calculate_profitability()}")



def main():
    folder_path = "C:\\Users\\User\\Documents\\python-projects\\trading\\v5\\backtest_data_new"
    
    backtest_files = [
        os.path.join(folder_path, filename)
        for filename in os.listdir(folder_path)
        if filename.endswith(".csv")
    ]

    percents=[(1, 2), (2, 2), (5, 10), (4, 10), (3, 10), (5, 20), (10, 20)]

    for tuple in percents:
        fetching_strategy = BinanceFetchStrategy()
        trading_strategy = OldStrategy(tuple[0], tuple[1])
        trading_strategy.binance = fetching_strategy.binance
        executor = StrategyExecutor(fetching_strategy, trading_strategy)

        for path in backtest_files:
            print(f"Running backtest for {path}")
            executor.execute_backtest(path)

if __name__ == "__main__":
    main()