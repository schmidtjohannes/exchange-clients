from binance import Client
import configparser
import pandas as pd
import time
from datetime import datetime
import math
import sys

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
    frame = pd.DataFrame(binance_client.get_historical_klines(coin, interval=INTERVAL_IN_MIN_BNC_UNIT, start_str="26 Nov, 2021", end_str="27 Nov, 2021"))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'High', 'Low', 'Open', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def MACD(df):
    df['EMA12'] = df.Close.ewm(span=12).mean()
    df['EMA26'] = df.Close.ewm(span=26).mean()
    df['MACD'] = df['EMA26'] - df['EMA12']
    df['signal'] = df.MACD.ewm(span=9).mean()

def get_current_sma_values(closes):
    return closes.iloc[0]['SMA_5'], closes.iloc[0]['SMA_8']

def get_current_close(df):
    return df.iloc[0]['Close']

def is_lower_than_previous(t, ohlc, current_close):
    previous_idx = ohlc.index.get_loc(t)
    if previous_idx == 0:
        return False

    previous_close = ohlc.iloc[previous_idx - 1]['Close']

    print("previous_idx " + str(previous_idx))
    print("current_close " + str(current_close))
    print("previous_close " + str(previous_close))
    print("ohlc.iloc[previous_idx - 2]['Close'] " + str(ohlc.iloc[previous_idx - 2]['Close']))
    if previous_idx >= 2:
        return current_close < previous_close and previous_close < ohlc.iloc[previous_idx - 2]['Close']
    else:
        return current_close < previous_close

def is_higher_than_previous(t, ohlc, current_close):
    previous_idx = ohlc.index.get_loc(t)
    if previous_idx == 0:
        return False
    previous_close = ohlc.iloc[previous_idx - 1]['Close']
    if previous_idx >= 2:
        return current_close > previous_close and previous_close > ohlc.iloc[previous_idx - 2]['Close']
    else:
        return current_close > previous_close

def test_sma():
    ohlc = get_ohlc_data(COIN['bot_pair'])
    buy_SMA_closes = SMA(ohlc)

    takeprofit = 1.015
    stoploss = 0.99

    trades = []
    buy_price = 0.0
    open_position = False
    trade = {}

    ctnBuy = 0
    ctnSell = 0
    for i, row in buy_SMA_closes.iterrows():
        print("")
        print("index as timestamp - " + str(i))
        shortTerm = row['SMA_5']
        longTerm = row['SMA_8']
        current_close = row['Close']
        print("shortTerm " + str(shortTerm))
        print("longTerm " + str(longTerm))
        print("current_close " + str(current_close))
        #if shortTerm >= longTerm and current_close >= shortTerm and not open_position:
        #if shortTerm >= (longTerm * 1.01) and current_close >= shortTerm and not open_position and not is_lower_than_previous(i, ohlc, current_close):
        #if shortTerm >= (longTerm * 1.01) and current_close >= shortTerm and not open_position:
        if not open_position and (
                (is_higher_than_previous(i, ohlc, current_close) and current_close > shortTerm) or
                (shortTerm >= (longTerm * 1.01) and current_close >= shortTerm)):
            print("***BUY***")
            ctnBuy += 1
            trade = {}
            buy_price = current_close
            open_position = True
            trade['buy_time'] = i
            trade['buy_price'] = buy_price
        elif open_position and (
                #shortTerm < (longTerm * 1.015) or
                current_close < buy_price * stoploss or
                current_close > buy_price * takeprofit):
            print("***SELL***")
            ctnSell += 1
            trade['sell_time'] = i
            trade['sell_price'] = current_close
            trade['profit'] = current_close - buy_price
            trade['profit_perc'] = (current_close - buy_price) / buy_price
            trades.append(trade)
            open_position = False
    profit = 0.0
    profitsrel = []
    for i in trades:
        profit += i['profit']
        profitsrel.append(i['profit_perc'])

    print("")
    print("TOTAL:")
    print("Buys: " + str(ctnBuy))
    print("Sellss: " + str(ctnSell))
    print("profit " + str(profit))
    print("profit in % " + str(profitsrel))

def test_macd():
    ohlc = get_ohlc_data(COIN['bot_pair'])

    MACD(ohlc)

    Buy, Sell = [],[]

    # skipp first 2 rows because MACD/signal is still 0 here
    for i in range(2, len(ohlc)):
        if ohlc.MACD.iloc[i] > ohlc.signal.iloc[i] and ohlc.MACD.iloc[i-1] < ohlc.signal.iloc[i-1]:
            Buy.append(i)
        elif ohlc.MACD.iloc[i] < ohlc.signal.iloc[i] and ohlc.MACD.iloc[i-1] > ohlc.signal.iloc[i-1]:
            Sell.append(i)

    Realbuys = [i+1 for i in Buy]
    Realsells = [i+1 for i in Sell]

    Buyprices = ohlc.Open.iloc[Realbuys]
    Sellprices = ohlc.Open.iloc[Realsells]

    if Sellprices.index[0] < Buyprices.index[0]:
        Sellprices = Sellprices.drop(Sellprices.index[0])
    if Buyprices.index[0] < Sellprices.index[0]:
        Buyprices = Buyprices.drop(Buyprices.index[0])

    # relative profit
    profitsrel = []
    profit = 0.0

    for i in range(len(Sellprices)):
        profitsrel.append((Sellprices[i] - Buyprices[i]) / Buyprices[i])
        profit += Sellprices[i] - Buyprices[i]

    print("")
    print("TOTAL:")
    print("Buys: " + str(len(Buyprices)))
    print("Sells: " + str(len(Sellprices)))
    print("profit " + str(profit))
    print("profit in % " + str(profitsrel))

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

    print("")
    print("backtest for " + COIN['asset'])
    print("")
    test_sma()
    test_macd()