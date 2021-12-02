from binance import Client
import configparser
import pandas as pd
import time
from datetime import datetime
import math
import sys
import os, psutil
import gc

INTERVAL_IN_MIN = 15
INTERVAL_IN_MIN_BNC_UNIT = Client.KLINE_INTERVAL_15MINUTE
INITIAL_DELAY_IN_MIN = INTERVAL_IN_MIN
SLEEP_INTERVAL_IN_SEC = 50
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

AVAILABLE_COINS = { 
    "MANA" : MANAUSDT_COIN ,
    "DOT" : DOTUSDT_COIN,
    "ETH" : ETHUSDT_COIN ,
    "LRC" : LRCUSDT_COIN ,
    "ENJ" : ENJUSDT_COIN ,
    "FLOW" : FLOWUSDT_COIN ,
    "IOTA" : IOTAUSDT_COIN ,
    "BLZ" : BLZUSDT_COIN ,
    "SAND" : SANDUSDT_COIN
}

COIN = {}

def print_memory():
    print("[TRACE] - Memory usage in MB: " + str(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2))
    print("")

def SMA(df):
    closes = pd.DataFrame(df['Close'])
    closes.columns = ['Close']
    for i in [SHORT_TERM, LONG_TERM]:
        sma = 'SMA_{}'.format(i)
        closes[sma] = closes.Close.rolling(i, min_periods=1).mean()
    # reverse list
    closes = closes.iloc[::-1]
    # drop NaN rows
    closes.dropna(inplace=True)
    return closes

def MACD(df):
    df['EMA12'] = df.Close.ewm(span=12).mean()
    df['EMA26'] = df.Close.ewm(span=26).mean()
    df['MACD'] = df['EMA26'] - df['EMA12']
    df['signal'] = df.MACD.ewm(span=9).mean()
    # reverse list
    df = df.iloc[::-1]
    # drop NaN rows
    df.dropna(inplace=True)
    return df

def get_ohlc_data(coin):
    # TODO define how many time frames are necessary to do SMA
    unixtime = time.time() - (60 * 60 * INTERVAL_IN_MIN)
    try:
        frame = pd.DataFrame(binance_client.get_historical_klines(coin, interval=INTERVAL_IN_MIN_BNC_UNIT, start_str=str(unixtime)))
    except:
        time.sleep(5)
        frame = pd.DataFrame(binance_client.get_historical_klines(coin, interval=INTERVAL_IN_MIN_BNC_UNIT, start_str=str(unixtime)))
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

def get_previous_sma_values(closes):
    return closes.iloc[1]['SMA_5'], closes.iloc[1]['SMA_8']

def get_current_sma_values(closes):
    return closes.iloc[0]['SMA_5'], closes.iloc[0]['SMA_8']

def is_higher_than_previous(ohlc, current_close):
    rev_ohlc = ohlc.iloc[::-1]
    previous_close = rev_ohlc.iloc[1]['Close']
    pre_previous_close = rev_ohlc.iloc[2]['Close']
    return current_close > previous_close and previous_close > pre_previous_close

def main(coin, qty, stoploss, takeprofit):
    open_position = False
    while True:
        print('\nCheck BUY at ' + get_time())
        ohlc = get_ohlc_data(coin)
        macd_frames = MACD(ohlc)
        time.sleep(1)
        current_close = get_current_close(coin)
        current_macd = macd_frames.MACD.iloc[0]
        current_signal = macd_frames.signal.iloc[0]
        previous_macd = macd_frames.MACD.iloc[1]
        previous_signal = macd_frames.signal.iloc[1]
        print('current_close ' + str(current_close))
        print('current_macd ' + str(current_macd))
        print('current_signal ' + str(current_signal))
        print('previous_macd ' + str(previous_macd))
        print('previous_signal ' + str(previous_signal))
        print_memory()
        del ohlc
        del macd_frames
        gc.collect()
        time.sleep(5)
        if not open_position and current_macd > current_signal and previous_macd < previous_signal:
            order = create_order(qty, side='BUY')
            print_memory()
            open_position = True
            time.sleep(SLEEP_INTERVAL_IN_SEC)
        if open_position:
            while True:
                print('\nCheck SELL at ' + get_time())
                print_memory()
                # let's wait one interval before start checking
                if order['transactTime'] + (60 * INITIAL_DELAY_IN_MIN) > time.time():
                    print('Sleep until initial INTERVAL is over')
                    time.sleep(INITIAL_DELAY_IN_MIN)
                    continue
                ohlc = get_ohlc_data(coin)
                macd_frames = MACD(ohlc)
                time.sleep(1)
                current_close = get_current_close(coin)
                print_memory()
                print_memory()
                print('current_close ' + str(current_close))
                print('order[price] ' + str(order['price']))
                current_macd = macd_frames.MACD.iloc[0]
                current_signal = macd_frames.signal.iloc[0]
                previous_macd = macd_frames.MACD.iloc[1]
                previous_signal = macd_frames.signal.iloc[1]
                print('current_close ' + str(current_close))
                print('current_macd ' + str(current_macd))
                print('current_signal ' + str(current_signal))
                print('previous_macd ' + str(previous_macd))
                print('previous_signal ' + str(previous_signal))
                del macd_frames
                del ohlc
                gc.collect()
                print_memory()
                if current_macd < current_signal and previous_macd > previous_signal:
                #if shortTerm < longTerm or current_close < order['price'] * stoploss or current_close > order['price'] * takeprofit:
                    # sell all you have
                    current_quantity = float(binance_client.get_asset_balance(COIN['asset'])['free'])
                    if not COIN['float_lot']:
                        current_quantity = math.floor(current_quantity)
                    order = create_order(current_quantity, side='SELL')
                    open_position = False
                    order = {}
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
    
    print_memory()
    if len(sys.argv) != 2:
        sys.exit("[ERROR] - No coin passed, avialable coins: " + str(list(AVAILABLE_COINS.keys())))

    coin_arg = sys.argv[1]
    if not coin_arg in AVAILABLE_COINS:
        sys.exit("[ERROR] - " + coin_arg + " is not in " + str(list(AVAILABLE_COINS.keys())))

    COIN = AVAILABLE_COINS[coin_arg]
    main(COIN['bot_pair'], COIN['quantity'], 0.99, 1.015)