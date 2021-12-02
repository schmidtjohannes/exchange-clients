from binance import Client
import configparser
import pandas as pd
import time
from datetime import datetime
import math
import sys
import ta
import numpy as np

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
    frame = pd.DataFrame(binance_client.get_historical_klines(coin, interval=INTERVAL_IN_MIN_BNC_UNIT, start_str="1 Nov, 2021", end_str="8 Nov, 2021"))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'High', 'Low', 'Open', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def get_micro_ohlc_data(coin):
    #frame = pd.DataFrame(binance_client.get_historical_klines(coin, interval=Client.KLINE_INTERVAL_1MINUTE, start_str="1 Nov, 2021", end_str="8 Nov, 2021"))
    frame = pd.DataFrame(binance_client.get_historical_klines(coin, Client.KLINE_INTERVAL_1MINUTE, "2 days ago"))
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

def is_higher_than_previous_simple(t, ohlc, current_close):
    previous_idx = ohlc.index.get_loc(t)
    if previous_idx == 0:
        return False
    previous_close = ohlc.iloc[previous_idx - 1]['Close']
    return current_close > previous_close

def test_sma():
    print("")
    print("Backtest test_sma")
    ohlc = get_ohlc_data(COIN['bot_pair'])
    buy_SMA_closes = SMA(ohlc)

    takeprofit = 1.02
    stoploss = 0.99

    trades = []
    buy_price = 0.0
    open_position = False
    trade = {}

    ctnBuy = 0
    ctnSell = 0
    trailing_loss_price = 0.0
    basic_takeprofit = 1000000.0
    skip = False
    print("amount of frames: " + str(len(buy_SMA_closes)))
    for i, row in buy_SMA_closes.iterrows():
        if skip:
            skip = False
            continue
        # print("")
        # print("index as timestamp - " + str(i))
        shortTerm = row['SMA_5']
        longTerm = row['SMA_8']
        current_close = row['Close']
        if open_position and current_close > trailing_loss_price and current_close > basic_takeprofit:
            trailing_loss_price = current_close
            #print("increasing trailing loss")
        #if open_position:
            #print("trailing_loss_price " + str(trailing_loss_price))
        # print("shortTerm " + str(shortTerm))
        # print("longTerm " + str(longTerm))
        # print("current_close " + str(current_close))
        #if shortTerm >= longTerm and current_close >= shortTerm and not open_position:
        #if shortTerm >= (longTerm * 1.01) and current_close >= shortTerm and not open_position and not is_lower_than_previous(i, ohlc, current_close):
        #if shortTerm >= (longTerm * 1.01) and current_close >= shortTerm and not open_position:
        if not open_position and (
                #(is_higher_than_previous(i, ohlc, current_close) and current_close > shortTerm) or
                #(shortTerm >= (longTerm * 1.01) and current_close >= shortTerm)):
                is_higher_than_previous_simple(i, ohlc, current_close) and
                shortTerm >= longTerm and current_close >= shortTerm):
            #print("***BUY*** at " + str(i) + " price " + str(current_close))
            ctnBuy += 1
            trade = {}
            buy_price = current_close
            trailing_loss_price = buy_price
            basic_takeprofit = buy_price * takeprofit
            open_position = True
            trade['buy_time'] = i
            trade['buy_price'] = buy_price
            skip = True
        elif open_position and (
                #shortTerm < (longTerm * 1.015) or
                current_close < trailing_loss_price * stoploss or
                current_close > trailing_loss_price * takeprofit or
                #current_close < buy_price * stoploss or
                #current_close > buy_price * takeprofit or
                current_close < longTerm):
            #print("***SELL*** at " + str(i) + " price " + str(current_close))
            ctnSell += 1
            trade['sell_time'] = i
            trade['sell_price'] = current_close
            trade['profit'] = current_close - buy_price
            trade['profit_perc'] = (current_close - buy_price) / buy_price
            trades.append(trade)
            open_position = False
            trailing_loss_price = 0.0
            basic_takeprofit = 1000000.0
            skip = False
            #print("profit in % " + str(trade['profit_perc']))
            #if current_close - buy_price < 0.0:
                #print("LOSS !!!")

    profit = 0.0
    profitsrel = 0.0
    for i in trades:
        profit += i['profit']
        profitsrel += i['profit_perc']

    print("")
    print("TOTAL:")
    print("Buys: " + str(ctnBuy))
    print("Sells: " + str(ctnSell))
    print("profit " + str(profit))
    print("profit in % " + str(profitsrel))

def test_macd():
    print("")
    print("Backtest test_macd")
    ohlc = get_ohlc_data(COIN['bot_pair'])

    MACD(ohlc)

    Buy, Sell = [],[]

    takeprofit = 1.015
    stoploss = 0.99

    # skipp first 2 rows because MACD/signal is still 0 here
    open_position = False
    buy_price = 0.0
    for i in range(2, len(ohlc)):
        current_close = ohlc.Close.iloc[i]
        if not open_position and ohlc.MACD.iloc[i] > ohlc.signal.iloc[i] and ohlc.MACD.iloc[i-1] < ohlc.signal.iloc[i-1]:
            Buy.append(i)
            open_position = True
            buy_price = current_close
        #elif open_position and ohlc.MACD.iloc[i] < ohlc.signal.iloc[i] and ohlc.MACD.iloc[i-1] > ohlc.signal.iloc[i-1]:
        elif open_position and (current_close < buy_price * stoploss or
                current_close > buy_price * takeprofit):
            Sell.append(i)
            open_position = False

    Realbuys = [i+1 for i in Buy]
    Realsells = [i+1 for i in Sell]

    Buyprices = ohlc.Open.iloc[Realbuys]
    Sellprices = ohlc.Open.iloc[Realsells]

    if Sellprices.index[0] < Buyprices.index[0]:
        Sellprices = Sellprices.drop(Sellprices.index[0])
    if Buyprices.index[0] < Sellprices.index[0]:
        Buyprices = Buyprices.drop(Buyprices.index[0])

    # relative profit
    profitsrel = 0.0
    profit = 0.0

    for i in range(min(len(Sellprices), len(Buyprices))):
        profitsrel += (Sellprices[i] - Buyprices[i]) / Buyprices[i]
        profit += Sellprices[i] - Buyprices[i]

    print("")
    print("TOTAL:")
    print("Buys: " + str(len(Buyprices)))
    print("Sells: " + str(len(Sellprices)))
    print("profit " + str(profit))
    print("profit in % " + str(profitsrel))

def test_micro_rsi_macd():
    print("")
    print("Backtest test_micro_rsi_macd")
    ohlc = get_micro_ohlc_data(COIN['bot_pair'])
    ohlc['%K'] = ta.momentum.stoch(ohlc.High, ohlc.Low, ohlc.Close, window=14, smooth_window=3)
    ohlc['%D'] = ohlc['%K'].rolling(3).mean()
    ohlc['rsi'] = ta.momentum.rsi(ohlc.Close, window=14)
    ohlc['macd'] = ta.trend.macd_diff(ohlc.Close)
    ohlc.dropna(inplace=True)
    

    takeprofit = 1.015
    stoploss = 0.995

    trades = []
    buy_price = 0.0
    open_position = False
    trade = {}

    ctnBuy = 0
    ctnSell = 0
    skip = False
    trailing_loss_price = 0.0
    basic_takeprofit = 1000000.0

    #for i, row in ohlc.iterrows():
    lags = 5
    for i in range(lags, (len(ohlc) -1)):
        if skip:
            skip = False
            continue
        #if open_position and current_close > trailing_loss_price and current_close > basic_takeprofit:
        #   trailing_loss_price = current_close
        sub_ohlc = ohlc.iloc[i:len(ohlc) -1]
        sub_ohlc = sub_ohlc.iloc[::-1]
        current_close = ohlc.iloc[i]['Close']
        sig = Signals(sub_ohlc, lags)
        sig.decide()
        if not open_position and (
                sub_ohlc.Buy.iloc[-1]):
            print("***BUY*** at " + str(i))
            ctnBuy += 1
            trade = {}
            buy_price = current_close
            open_position = True
            skip = True
            trade['buy_time'] = i
            trade['buy_price'] = buy_price
            trailing_loss_price = buy_price
            basic_takeprofit = buy_price * takeprofit
        elif open_position and (
                current_close < trailing_loss_price * stoploss or
                current_close > trailing_loss_price * takeprofit):
            print("***SELL*** at " + str(i))
            ctnSell += 1
            trade['sell_time'] = i
            trade['sell_price'] = current_close
            trade['profit'] = current_close - buy_price
            trade['profit_perc'] = (current_close - buy_price) / buy_price
            trades.append(trade)
            open_position = False
            trailing_loss_price = 0.0
            basic_takeprofit = 1000000.0
    profit = 0.0
    profitsrel = 0.0
    for i in trades:
        profit += i['profit']
        profitsrel += i['profit_perc']

    print("")
    print("TOTAL:")
    print("Buys: " + str(ctnBuy))
    print("Sells: " + str(ctnSell))
    print("profit " + str(profit))
    print("profit in % " + str(profitsrel))

def test_micro_sma():
    print("")
    print("Backtest test_micro_sma")
    ohlc = get_micro_ohlc_data(COIN['bot_pair'])
    buy_SMA_closes = SMA(ohlc)

    takeprofit = 1.02
    stoploss = 0.99

    trades = []
    buy_price = 0.0
    open_position = False
    trade = {}

    ctnBuy = 0
    ctnSell = 0
    skip = False
    trailing_loss_price = 0.0
    basic_takeprofit = 1000000.0
    for i, row in buy_SMA_closes.iterrows():
        if skip:
            skip = False
            continue
        # print("")
        # print("index as timestamp - " + str(i))
        if open_position and current_close > trailing_loss_price and current_close > basic_takeprofit:
            trailing_loss_price = current_close
        shortTerm = row['SMA_5']
        longTerm = row['SMA_8']
        current_close = row['Close']
        # print("shortTerm " + str(shortTerm))
        # print("longTerm " + str(longTerm))
        # print("current_close " + str(current_close))
        if not open_position and (
                is_higher_than_previous_simple(i, ohlc, current_close) and
                current_close > shortTerm and
                shortTerm > longTerm):
            print("***BUY*** at " + str(i))
            ctnBuy += 1
            trade = {}
            buy_price = current_close
            open_position = True
            skip = True
            trade['buy_time'] = i
            trade['buy_price'] = buy_price
            trailing_loss_price = buy_price
            basic_takeprofit = buy_price * takeprofit
        elif open_position and (
                current_close < shortTerm or
                current_close < trailing_loss_price * stoploss or
                current_close > trailing_loss_price * takeprofit):
            print("***SELL*** at " + str(i))
            ctnSell += 1
            trade['sell_time'] = i
            trade['sell_price'] = current_close
            trade['profit'] = current_close - buy_price
            trade['profit_perc'] = (current_close - buy_price) / buy_price
            trades.append(trade)
            open_position = False
            trailing_loss_price = 0.0
            basic_takeprofit = 1000000.0
    profit = 0.0
    profitsrel = 0.0
    for i in trades:
        profit += i['profit']
        profitsrel += i['profit_perc']

    print("")
    print("TOTAL:")
    print("Buys: " + str(ctnBuy))
    print("Sellss: " + str(ctnSell))
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
    #test_sma()
    #time.sleep(5)
    test_micro_rsi_macd()
    #time.sleep(5)
    #test_macd()