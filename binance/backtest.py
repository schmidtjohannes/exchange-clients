from binance import Client
import configparser
import pandas as pd
import time
from datetime import datetime
import math

INTERVAL_IN_MIN = 30
INTERVAL_IN_MIN_BNC_UNIT = Client.KLINE_INTERVAL_15MINUTE

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

COIN = SANDUSDT_COIN

def SMA(df):

    for i in [5,8]:
        sma = 'SMA_{}'.format(i)
        df[sma] = df.Close.rolling(i, min_periods=1).mean()
    #reverse list
    #df = df.iloc[::-1]

    # drop NaN rows
    df.dropna(inplace=True)
    return df

def get_ohlc_data(coin):
    unixtime = time.time() - (60 * 60 * INTERVAL_IN_MIN)
    try:
        frame = pd.DataFrame(binance_client.get_historical_klines(coin, interval=INTERVAL_IN_MIN_BNC_UNIT, start_str="26 Nov, 2021", end_str="27 Nov, 2021"))
    except:
        time.sleep(5)
        frame = pd.DataFrame(binance_client.get_historical_klines(coin, interval=INTERVAL_IN_MIN_BNC_UNIT, start_str="26 Nov, 2021", end_str="27 Nov, 2021"))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'High', 'Low', 'Open', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def get_current_sma_values(closes):
    return closes.iloc[0]['SMA_5'], closes.iloc[0]['SMA_8']

def get_current_close(df):
    return df.iloc[0]['Close']

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    print("")
    print("backtest for " + COIN['asset'])
    print("")

    ohlc = get_ohlc_data(COIN['bot_pair'])

    buy_SMA_closes = SMA(ohlc)

    takeprofit = 1.015
    stoploss = 0.99

    trades = []
    buy_price = 0.0
    open_position = False
    trade = {}
    for i, row in buy_SMA_closes.iterrows():
        shortTerm = row['SMA_5']
        longTerm = row['SMA_8']
        current_close = row['Close']
        if shortTerm >= longTerm and current_close >= shortTerm and not open_position:
            trade = {}
            buy_price = current_close
            open_position = True
            trade['buy_time'] = i
            trade['buy_price'] = buy_price
        elif open_position and (shortTerm < longTerm or current_close < buy_price * stoploss or current_close > buy_price * takeprofit):
            trade['sell_time'] = i
            trade['sell_price'] = current_close
            trade['profit'] = current_close - buy_price
            trade['profit_perc'] = (current_close - buy_price) / buy_price
            trades.append(trade)
            open_position = False
    profit = 0.0
    profit_perc = 0.0
    for i in trades:
        profit += i['profit']
        profit_perc += i['profit_perc']

    print("profit " + str(profit))
    print("profit in % " + str(profit_perc))