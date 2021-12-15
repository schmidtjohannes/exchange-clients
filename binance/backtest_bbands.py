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

QTY = 500

MATICBNB_COIN = {
  "bot_pair": "MATICBNB",
  "quantity": QTY,
  "asset": "MATIC",
  "float_lot": False
}

AVAILABLE_COINS = { 
    "MATIC" : MATICBNB_COIN
}

COIN = {}



def get_ohlc_data(coin):
    frame = pd.DataFrame(binance_client.get_historical_klines(coin, Client.KLINE_INTERVAL_1MINUTE, "24 hours ago"))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'High', 'Low', 'Open', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def get_bbands(df):
    indicator_bb = ta.volatility.BollingerBands(
                                df.Close,
                                window=21,
                                window_dev=2)
    df['bbands_upper'] = indicator_bb.bollinger_hband()
    df['bbands_middle'] = indicator_bb.bollinger_mavg()
    df['bbands_lower'] = indicator_bb.bollinger_lband()

def test_bbands():
    print("")
    print("Backtest test_bollinger bands")
    ohlc = get_ohlc_data(COIN['bot_pair'])
    get_bbands(ohlc)

    trades = []
    buy_price = 0.0
    open_position = False
    trade = {}

    ctnBuy = 0
    ctnSell = 0
    ticker = binance_client.get_symbol_ticker(symbol="BNBUSDT")
    current_bnb = float(ticker['price'])
    print("amount of frames: " + str(len(ohlc)))
    for i, row in ohlc.iterrows():
        # print("")
        # print("index as timestamp - " + str(i))
        upper = row['bbands_upper']
        lower = row['bbands_lower']
        middle = row['bbands_middle']
        current_close = row['Close']

        # print("middle " + str(middle))
        # print("upper " + str(upper))
        # print("lower " + str(lower))
        # print("current_close " + str(current_close))
        # print("Stop loss " + str(buy_price * stoploss))
        # print("Take profit " + str(buy_price * takeprofit))
        if not open_position and (
                current_close < middle):
            # print("***BUY*** at " + str(i) + " price " + str(current_close))
            ctnBuy += 1
            trade = {}
            buy_price = current_close
            open_position = True
            trade['buy_time'] = i
            trade['buy_price'] = buy_price
        elif open_position and (
                current_close > upper or
                current_close < lower):
                # current_close < buy_price * stoploss or
                # current_close > buy_price * takeprofit):
            # print("***SELL*** at " + str(i) + " price " + str(current_close))
            ctnSell += 1
            trade['sell_time'] = i
            trade['sell_price'] = current_close
            trade['profit'] = ((current_close * QTY) - (buy_price * QTY)) * current_bnb
            trade['profit_perc'] = (current_close - buy_price) / buy_price
            trades.append(trade)
            open_position = False

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
    test_bbands()
