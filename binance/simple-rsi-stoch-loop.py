from binance import Client
import configparser
import pandas as pd
import ta
import time
import numpy as np
from datetime import datetime
import math
import sys

INTERVAL_IN_MIN = 1
INTERVAL_IN_MIN_BNC_UNIT = Client.KLINE_INTERVAL_1MINUTE
INITIAL_DELAY_IN_MIN = INTERVAL_IN_MIN
SLEEP_INTERVAL_IN_SEC = 5
SHORT_TERM = 5
LONG_TERM = 8

ETHUSDT_COIN = {
  "bot_pair": "ETHUSDT",
  "quantity": 0.001,
  "asset": "ETH",
  "float_lot": True
}

DOTUSDT_COIN = {
  "bot_pair": "DOTUSDT",
  "quantity": 1,
  "asset": "DOT",
  "float_lot": True
}
# Non altcoin
MANAUSDT_COIN = {
  "bot_pair": "MANAUSDT",
  "quantity": 10,
  "asset": "MANA",
  "float_lot": False
}
# Non altcoin
LRCUSDT_COIN = {
  "bot_pair": "LRCUSDT",
  "quantity": 15,
  "asset": "LRC",
  "float_lot": False
}
# Non altcoin
ENJUSDT_COIN = {
  "bot_pair": "ENJUSDT",
  "quantity": 4,
  "asset": "ENJ",
  "float_lot": False
}
# Non altcoin
FLOWUSDT_COIN = {
  "bot_pair": "FLOWUSDT",
  "quantity": 0.2,
  "asset": "FLOW",
  "float_lot": True
}

IOTAUSDT_COIN = {
  "bot_pair": "IOTAUSDT",
  "quantity": 2,
  "asset": "IOTA",
  "float_lot": False
}

BLZUSDT_COIN = {
  "bot_pair": "BLZUSDT",
  "quantity": 30,
  "asset": "BLZ",
  "float_lot": False
}

SANDUSDT_COIN = {
  "bot_pair": "SANDUSDT",
  "quantity": 2,
  "asset": "SAND",
  "float_lot": False
}

MATICUSDT_COIN = {
  "bot_pair": "MATICUSDT",
  "quantity": 10,
  "asset": "MATIC",
  "float_lot": False
}

AVAILABLE_COINS = { 
    "MANA" : MANAUSDT_COIN ,
    "DOT" : DOTUSDT_COIN,
    "ETH" : ETHUSDT_COIN ,
    "LRC" : LRCUSDT_COIN ,
    "ENJ" : ENJUSDT_COIN ,
    "FLOW" : FLOWUSDT_COIN ,
    "IOTA" : IOTAUSDT_COIN ,
    "BLZ" : BLZUSDT_COIN ,
    "SAND" : SANDUSDT_COIN ,
    "MATIC" : MATICUSDT_COIN
}

COIN = {}

class Signals:
    def __init__(self, df, lags):
        self.df = df
        self.lags = lags
    
    def gettrigger(self):
        dfx = pd.DataFrame()
        for i in range(1,self.lags+1):
                mask = (self.df['%K'].shift(i) < 20) & (self.df['%D'].shift(i) < 20)
                dfx = dfx.append(mask, ignore_index=True)
        return dfx.sum(axis=0)

    def decide(self):
        self.df['trigger'] = np.where(self.gettrigger(), 1, 0)
        self.df['Buy'] = np.where((self.df.trigger) & (self.df['%K'].between(20,80)) & (self.df['%D'].between(20,80))
                            & (self.df.rsi > 50) & (self.df.macd > 0), 1, 0)

def add_stats(ohlc):
    ohlc['%K'] = ta.momentum.stoch(ohlc.High, ohlc.Low, ohlc.Close, window=14, smooth_window=3)
    ohlc['%D'] = ohlc['%K'].rolling(3).mean()
    ohlc['rsi'] = ta.momentum.rsi(ohlc.Close, window=14)
    ohlc['macd'] = ta.trend.macd_diff(ohlc.Close)
    # drop NaN rows
    ohlc.dropna(inplace=True)

def get_ohlc_data(coin):
    try:
        frame = pd.DataFrame(binance_client.get_historical_klines(coin, INTERVAL_IN_MIN_BNC_UNIT, "100 min ago"))
    except:
        time.sleep(5)
        frame = pd.DataFrame(binance_client.get_historical_klines(coin, INTERVAL_IN_MIN_BNC_UNIT, "100 min ago"))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'High', 'Low', 'Open', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def get_time():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def get_current_close(coin):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=coin)
    except:
        time.sleep(5)
        ticker = binance_client.get_symbol_ticker(symbol=coin)
    return float(ticker['price'])

def create_order(quantity, side='BUY', leverage=None):
    print('create '+ side +' order via API')
    order = binance_client.create_order(symbol=COIN['bot_pair'],
        side=side,
        type='MARKET',
        quantity=quantity)
    order['transactTime'] = time.time()
    order['price'] = float(order['fills'][0]['price'])
    return order

def main(coin, qty, stoploss, takeprofit):
    open_position = False
    trailing_loss_price = 0.0
    basic_takeprofit = 1000000.0
    buy_price = 0.0
    while True:
        print('\nCheck BUY at ' + get_time())
        ohlc = get_ohlc_data(coin)
        add_stats(ohlc)
        sig = Signals(ohlc, 3)
        sig.decide()
        time.sleep(1)
        current_close = ohlc.Close.iloc[-1]

        print('current_close ' + str(current_close))
        print("ohlc.Buy.iloc[-1] " + str(ohlc.Buy.iloc[-1]))
        if not open_position and (
                ohlc.Buy.iloc[-1]):
            order = create_order(qty, side='BUY')
            open_position = True
            time.sleep(SLEEP_INTERVAL_IN_SEC)
            trailing_loss_price = order['price']
            basic_takeprofit = order['price'] * takeprofit
            buy_price = order['price']
        if open_position:
            while True:
                print('\nCheck SELL at ' + get_time())

                # let's wait one interval before start checking
                if order['transactTime'] + (60 * INITIAL_DELAY_IN_MIN) > time.time():
                    print('Sleep until initial INTERVAL is over')
                    time.sleep(INITIAL_DELAY_IN_MIN)
                    continue
                ohlc = get_ohlc_data(coin)
                current_close = ohlc.Close.iloc[-1]

                #if open_position and current_close > trailing_loss_price and current_close > basic_takeprofit:
                #    trailing_loss_price = current_close
                print(f'current close ' + str(current_close))
                print(f'current target ' + str(trailing_loss_price * takeprofit))
                print(f'current stop ' + str(trailing_loss_price * stoploss))
                #if current_close < trailing_loss_price * stoploss or current_close > trailing_loss_price * takeprofit:
                if current_close < trailing_loss_price * stoploss or current_close > trailing_loss_price * takeprofit:
                    # sell all you have
                    current_quantity = float(binance_client.get_asset_balance(COIN['asset'])['free'])
                    if not COIN['float_lot']:
                        current_quantity = math.floor(current_quantity)
                    order = create_order(current_quantity, side='SELL')
                    open_position = False
                    order = {}
                    trailing_loss_price = 0.0
                    basic_takeprofit = 1000000.0
                    buy_price = 0.0
                    break
                time.sleep(SLEEP_INTERVAL_IN_SEC)
        # TODO each min
        time.sleep(SLEEP_INTERVAL_IN_SEC)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    if len(sys.argv) != 2:
        sys.exit("[ERROR] - No coin passed, avialable coins: " + str(list(AVAILABLE_COINS.keys())))

    coin_arg = sys.argv[1]
    if not coin_arg in AVAILABLE_COINS:
        sys.exit("[ERROR] - " + coin_arg + " is not in " + str(list(AVAILABLE_COINS.keys())))

    COIN = AVAILABLE_COINS[coin_arg]
    main(COIN['bot_pair'], COIN['quantity'], 0.996, 1.004)
